from typing import Iterator

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers.html2text import Html2TextTransformer
from pydantic import AnyUrl

from sokhan.data_entry.base.crawlers import BaseCrawler, BaseFeedCrawler
from sokhan.data_entry.domain.custom.documents import CustomArticleDocument


class CustomArticleCrawler(BaseCrawler):
    def __init__(self):
        self._html2text_model = Html2TextTransformer()

    def extract(self, url: AnyUrl) -> list[CustomArticleDocument]:
        return self.extract_urls([url])[0]

    def extract_urls(self, urls: list[AnyUrl]) -> list[CustomArticleDocument]:
        out = []
        loader = AsyncHtmlLoader(urls)
        docs = loader.load()

        docs_transformed = self._html2text_model.transform_documents(docs)

        for i in range(len(docs_transformed)):
            doc_transformed = docs_transformed[0]

            out.append(CustomArticleDocument(url=urls[i],
                                             title=doc_transformed.metadata["title"],
                                             description=doc_transformed.metadata["description"],
                                             language=doc_transformed.metadata["language"],
                                             content=doc_transformed.page_content
                                             )
                       )


class CustomProfileCrawler(BaseCrawler):
    def extract(self, url: AnyUrl) -> list[AnyUrl]:
        raise NotImplementedError()


class CustomFeedCrawler(BaseFeedCrawler):
    def extract(self, url: AnyUrl) -> Iterator[list[AnyUrl]]:
        raise NotImplementedError()
