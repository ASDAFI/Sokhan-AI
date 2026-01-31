from abc import ABC, abstractmethod

from pydantic import AnyUrl

from sokhan.data_entry.base.documents import Document



class BaseCrawler(ABC):
    model: type[Document]

    @abstractmethod
    def extract(self, url: AnyUrl) -> Document:
        pass

class BaseProfileCrawler(ABC):
    @abstractmethod
    def extract(self, profile_url: AnyUrl) -> list[AnyUrl]:
        pass
