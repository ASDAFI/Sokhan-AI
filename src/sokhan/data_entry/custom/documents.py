from pydantic import AnyUrl

from sokhan.data_entry.base.documents import Document

class CustomArticleDocument(Document):
    url: AnyUrl
    title: str
    description: str
    language: str
    content: str

    @property
    def collection_name(self):
        return "custom_articles"
