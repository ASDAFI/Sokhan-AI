from abc import ABC, abstractmethod
from typing import Iterator

from pydantic import AnyUrl

from sokhan.data_entry.base.documents import Document


class BaseCrawler(ABC):
    model: type[Document]

    @abstractmethod
    def extract(self, url: AnyUrl) -> Document:
        pass

    @abstractmethod
    def extract_urls(self, url: list[AnyUrl]) -> list[Document]:
        pass


class BaseProfileCrawler(ABC):
    @abstractmethod
    def extract(self, profile_url: AnyUrl) -> list[AnyUrl]:
        pass


class BaseFeedCrawler(ABC):
    @abstractmethod
    def extract(self, home_page: AnyUrl, min_date: str) -> Iterator[list[AnyUrl]]:
        pass
