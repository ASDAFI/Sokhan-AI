from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers.html2text import Html2TextTransformer
from pydantic import AnyUrl

from sokhan.entry.base.crawlers import BaseCrawler
from sokhan.entry.custom.documents import CustomArticleDocument


class CustomArticleCrawler(BaseCrawler):
    def __init__(self):
        self._html2text_model = Html2TextTransformer()

    def extract(self, url: AnyUrl) -> CustomArticleDocument:
        loader = AsyncHtmlLoader([url])
        docs = loader.load()

        docs_transformed = self._html2text_model.transform_documents(docs)
        doc_transformed = docs_transformed[0]

        return CustomArticleDocument(url=url,
                                     title=doc_transformed.metadata["title"],
                                     description=doc_transformed.metadata["description"],
                                     language=doc_transformed.metadata["language"],
                                     content=doc_transformed.page_content
                                     )

class CustomProfileCrawler(BaseCrawler):
    def extract(self, url: AnyUrl) -> list[AnyUrl]:
        raise NotImplementedError()

