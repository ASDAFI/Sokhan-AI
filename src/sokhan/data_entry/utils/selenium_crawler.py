import time
from abc import ABC

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


class BaseSeleniumCrawler(ABC):
    def __init__(self, headless: bool = True, timeout: int = 10):
        self.timeout = timeout
        self._setup_driver(headless)

    def _setup_driver(self, headless: bool):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.driver:
            self.driver.quit()

    def load_page(self, url: str, wait_element_selector: str | None = None):
        logger.info(f"Loading: {url}")
        self.driver.get(url)
        if wait_element_selector:
            self.wait_for_element(wait_element_selector)

    def wait_for_element(self, selector: str, by: str = By.CSS_SELECTOR):
        try:
            return WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {selector}")
            return None

    def click_element(self, selector: str, by: str = By.CSS_SELECTOR):
        try:
            element = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
            logger.info(f"Clicked: {selector}")
        except Exception as e:
            logger.error(f"Click failed: {e}")

    def get_html(self) -> str:
        return self.driver.page_source
