from sokhan.data_entry.base.crawlers import BaseCrawler, BaseProfileCrawler, BaseFeedCrawler
from sokhan.data_entry.domain.custom.crawlers import CustomArticleCrawler, CustomProfileCrawler, CustomFeedCrawler
from sokhan.data_entry.domain.git.crawlers import GitCrawler
from sokhan.data_entry.dispatcher import BaseDispatcher
from sokhan.data_entry.domain.tasnim.crawlers import TasnimHomePageCrawler, TasnimArticleCrawler
from sokhan.data_entry.domain.virgool.crawlers import VirgoolProfileCrawler


class CrawlerDispatcher(BaseDispatcher[BaseCrawler]):

    @classmethod
    def create_default(cls) -> "CrawlerDispatcher":
        return (
            cls.builder()
            .register("https://github.com", GitCrawler)
            .register("https://tasnimnews.ir", TasnimArticleCrawler)
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


class FeedCrawlerDispatcher(BaseDispatcher[BaseFeedCrawler]):

    @classmethod
    def create_default(cls) -> "ProfileCrawlerDispatcher":
        return (
            cls.builder()
            .register("https://tasnimnews.ir", TasnimHomePageCrawler)
            .set_default(CustomFeedCrawler)
            .build()
        )
