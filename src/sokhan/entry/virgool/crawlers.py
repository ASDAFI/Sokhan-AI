import re

from langchain_community.document_loaders import AsyncHtmlLoader
from pydantic import AnyUrl

from sokhan.entry.base.crawlers import BaseProfileCrawler


class VirgoolProfileCrawler(BaseProfileCrawler):
    def extract(self, profile_url: AnyUrl) -> list[AnyUrl]:
        loader = AsyncHtmlLoader([profile_url])
        docs = loader.load()
        doc = docs[0]

        content = doc.page_content

        pattern = r'https://virgool\.io/@[a-zA-Z0-9_]+/[a-zA-Z0-9%_\-]+'

        matches = re.findall(pattern, content)
        return matches
