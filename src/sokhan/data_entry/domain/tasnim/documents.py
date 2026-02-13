from pydantic import AnyUrl

from sokhan.data_entry.base.documents import Document


class TasnimNews(Document):
    url: AnyUrl
    title: str
    content: str
    shamsi_date: str
    date: str
    keywords: list[str]

    @property
    def collection_name(self):
        return "tasnim_news"
