import re
from typing import Type, TypeVar, Generic

from pydantic import AnyUrl
from loguru import logger

from sokhan.entry.utils.general import get_domain

T = TypeVar('T')
TCrawler = TypeVar('TCrawler')
TProfileCrawler = TypeVar('TProfileCrawler')


class DispatcherBuilder(Generic[T]):
    def __init__(self):
        self._patterns: list[tuple[str, Type[T]]] = []
        self._default_crawler: Type[T] = None

    def register(self, domain: AnyUrl, crawler: Type[T]) -> "DispatcherBuilder[T]":
        """Register a crawler for a specific domain pattern."""
        domain_str = get_domain(domain)
        pattern = r"https://(www\.)?{}/*".format(re.escape(domain_str))
        self._patterns.append((pattern, crawler))
        return self

    def set_default(self, default_crawler: Type[T]) -> "DispatcherBuilder[T]":
        """Set the default crawler for unmatched URLs."""
        self._default_crawler = default_crawler
        return self

    def build(self) -> "BaseDispatcher[T]":
        """Build and return a configured dispatcher instance."""
        if not self._default_crawler:
            raise ValueError("Default crawler must be set before building")

        dispatcher = BaseDispatcher[T]()
        dispatcher._crawlers = dict(self._patterns)
        dispatcher._default_crawler = self._default_crawler
        return dispatcher


class BaseDispatcher(Generic[T]):
    def __init__(self):
        self._crawlers: dict[str, Type[T]] = {}
        self._default_crawler: Type[T] = None

    def get_crawler(self, url: AnyUrl) -> T:
        for pattern, crawler in self._crawlers.items():
            if re.match(pattern, url):
                return crawler()

        logger.warning("No crawler found for {}".format(url))
        return self._default_crawler()

    @classmethod
    def builder(cls) -> DispatcherBuilder[T]:
        """Create a builder for configuring the dispatcher."""
        return DispatcherBuilder[T]()

