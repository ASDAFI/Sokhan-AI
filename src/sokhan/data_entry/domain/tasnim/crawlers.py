from typing import Iterator

import jdatetime
from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncHtmlLoader
from pydantic import AnyUrl
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from sokhan.data_entry.base.crawlers import BaseCrawler, BaseFeedCrawler
from sokhan.data_entry.utils.selenium_crawler import BaseSeleniumCrawler
from sokhan.data_entry.base.documents import Document
from sokhan.data_entry.domain.tasnim.documents import TasnimNews
from sokhan.utils.general import from_jalali_to_gregorian

PERSIAN_MONTHS = {
    "فروردین": "01", "اردیبهشت": "02", "خرداد": "03",
    "تیر": "04", "مرداد": "05", "شهریور": "06",
    "مهر": "07", "آبان": "08", "آذر": "09",
    "دی": "10", "بهمن": "11", "اسفند": "12"
}


def _fix_time_field(time_field: str) -> str:
    if "ساعت پیش" in time_field:
        hour = int(time_field.split()[0])
        today = jdatetime.date.today() - jdatetime.timedelta(hours=hour)
    elif "دقیقه پیش" in time_field:
        minute = int(time_field.split()[0])
        today = jdatetime.date.today() - jdatetime.timedelta(minutes=minute)
    else:
        return _fix_shamsi_date(time_field)

    return today.strftime("%Y-%m-%d %H:%M")


def _fix_shamsi_date(shamsi_date: str) -> str:
    parts = shamsi_date.split(" ")
    return f"{parts[2]}-{PERSIAN_MONTHS[parts[1]]}-{parts[0]} {parts[4]}"


def _get_corresponding_gregorian_date(shamsi_cleaned_date: str) -> str:
    year, month, day_hour = shamsi_cleaned_date.split("-")
    day, hour = day_hour.split()
    gre_date = from_jalali_to_gregorian(int(year), int(month), int(day))

    return f"{gre_date.year}-{gre_date.month}-{gre_date.day} {hour}"


class TasnimArticleCrawler(BaseCrawler):
    @staticmethod
    def __extract_date(soup: BeautifulSoup) -> str:
        time_tag = soup.select_one('ul.details li.time')
        shamsi_date_str = ""
        if time_tag:
            shamsi_date_str = " ".join(time_tag.get_text().split())
        return shamsi_date_str

    @staticmethod
    def __extract_title(soup: BeautifulSoup) -> str:
        title_tag = soup.select_one('h1.title')
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        return title

    @staticmethod
    def __extract_keywords(soup: BeautifulSoup) -> list[str]:
        keywords = []
        service_tags = soup.select('ul.details li.service a')
        for tag in service_tags:
            text = tag.get_text(strip=True)
            if text:
                keywords.append(text)
        return keywords

    @staticmethod
    def __extract_content(soup: BeautifulSoup) -> str:
        lead_tag = soup.select_one('h3.lead')
        lead_text = lead_tag.get_text(strip=True) if lead_tag else ""

        story_div = soup.select_one('div.story')
        body_text = ""

        if story_div:
            for noise in story_div.select('.hideTag, .clearfix'):
                noise.decompose()

            paragraphs = [p.get_text(strip=True) for p in story_div.find_all('p')]
            body_text = "\n\n".join(paragraphs)

        full_content = f"{lead_text}\n\n{body_text}".strip()
        return full_content

    def _extract_from_html(self, raw_html: str, url: AnyUrl) -> TasnimNews:
        soup = BeautifulSoup(raw_html, 'html.parser')

        shamsi_date_str = _fix_time_field(self.__extract_date(soup))
        gre_date_str = _get_corresponding_gregorian_date(shamsi_date_str)

        return TasnimNews(
            url=url,
            title=self.__extract_title(soup),
            content=self.__extract_content(soup),
            shamsi_date=shamsi_date_str,
            date=gre_date_str,
            keywords=self.__extract_keywords(soup)
        )

    def extract_urls(self, urls: list[AnyUrl]) -> list[TasnimNews]:
        out = []
        loader = AsyncHtmlLoader(urls)
        docs = loader.load()

        for i in range(len(docs)):
            raw_html = docs[i].page_content
            out.append(self._extract_from_html(raw_html, urls[i]))
        return out

    def extract(self, url: AnyUrl) -> Document:
        return self.extract_urls([url])[0]


class TasnimHomePageCrawler(BaseFeedCrawler, BaseSeleniumCrawler):
    def __init__(self, headless: bool = True, timeout: int = 10):
        super().__init__(headless, timeout)
        self.load_more_selector = "loadMore"
        self.feed_container_selector = "article.list-item "

    def extract(self, url: str,
                min_date: str = "1404-11-24 00:00",
                max_clicks: int = 5) -> Iterator[list[str]]:

        self.load_page(url, wait_element_selector=self.feed_container_selector)

        seen_links = set()
        clicks = 0
        processed_count = 0

        while True:
            all_feeds = self._get_feed_elements()

            new_feeds_elements = all_feeds[processed_count:]

            logger.info(f"Processing {len(new_feeds_elements)} new feeds (Total visible: {len(all_feeds)})")

            parsed_data = self._parse_feeds(new_feeds_elements)

            current_batch = []
            all_visible_new = True

            for link, raw_date_text in parsed_data:
                try:
                    comparable_date = _fix_time_field(raw_date_text)

                    if comparable_date >= min_date:
                        if link not in seen_links:
                            seen_links.add(link)
                            current_batch.append(link)
                    else:
                        all_visible_new = False
                except Exception as e:
                    logger.warning(f"Failed to parse date '{raw_date_text}': {e}")
                    continue

            if current_batch:
                yield current_batch

            processed_count = len(all_feeds)

            if not all_visible_new:
                logger.info("Found feed older than min_date. Stopping extraction.")
                break

            if clicks >= max_clicks:
                logger.info(f"Reached max clicks ({max_clicks}). Stopping extraction.")
                break

            if not self._load_more(previous_count=processed_count):
                logger.info("No more content to load.")
                break

            clicks += 1

    def _get_feed_elements(self) -> list[WebElement]:
        return self.driver.find_elements(By.CSS_SELECTOR, self.feed_container_selector)

    def _parse_feeds(self, elements: list[WebElement]) -> list[tuple[str, str]]:
        data = []
        for el in elements:
            try:
                try:
                    link_el = el.find_element(By.CSS_SELECTOR, "h2.title a")
                except NoSuchElementException:
                    link_el = el.find_element(By.TAG_NAME, "a")

                url = link_el.get_attribute("href")

                date_el = el.find_element(By.TAG_NAME, "time")
                raw_date = date_el.text.strip()

                if url and raw_date:
                    data.append((url, raw_date))
            except Exception as e:
                logger.warning(f"Failed to parse feed : {e}")
        return data

    def _load_more(self, previous_count: int) -> bool:
        try:
            btn = self.driver.find_elements(By.ID, self.load_more_selector)
            if not btn:
                return False

            self.click_element(self.load_more_selector, By.ID)

            WebDriverWait(self.driver, self.timeout).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, self.feed_container_selector)) > previous_count
            )
            return True
        except (TimeoutException, Exception) as e:
            logger.error(f"Load more failed or timed out: {e}")
            return False
