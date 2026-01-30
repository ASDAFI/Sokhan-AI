from sokhan.entry.base.crawlers import BaseCrawler, BaseProfileCrawler
from sokhan.entry.custom.crawlers import CustomArticleCrawler, CustomProfileCrawler
from sokhan.entry.git.crawlers import GitCrawler
from sokhan.entry.dispatcher import BaseDispatcher
from sokhan.entry.virgool.crawlers import VirgoolProfileCrawler


class CrawlerDispatcher(BaseDispatcher[BaseCrawler]):

    @classmethod
    def create_default(cls) -> "CrawlerDispatcher":
        return (
            cls.builder()
            .register("https://github.com", GitCrawler)
            .set_default(CustomArticleCrawler)
            .build()
        )


class ProfileCrawlerDispatcher(BaseDispatcher[BaseProfileCrawler]):

    @classmethod
    def create_default(cls) -> "ProfileCrawlerDispatcher":
        return (
            cls.builder()
            .register("https://virgool.io", VirgoolProfileCrawler)
            .set_default(CustomProfileCrawler)
            .build()
        )