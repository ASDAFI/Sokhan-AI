from collections import defaultdict

from typing import Annotated
from zenml import get_step_context, step, pipeline

from sokhan.db.mongo_client import MongoDBClient
from sokhan.data_entry.base.documents import Document
from sokhan.data_entry.crawlers import CrawlerDispatcher, ProfileCrawlerDispatcher
from sokhan.data_entry.utils.general import get_domain


@step
def crawl_profile(profile_url: str) -> Annotated[list[str], "links"]:
    dispatcher = ProfileCrawlerDispatcher().create_default()
    links = dispatcher.get_crawler(profile_url).extract(profile_url)

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="links", metadata={"links": links})

    return links

@step
def crawl_links(links: list[str]) -> Annotated[list[Document], "docs"]:
    dispatcher = CrawlerDispatcher.create_default()
    metadata = defaultdict(lambda: {"success": [], "failure": []})

    docs = []

    for link in links:
        domain = get_domain(link)
        try:
            doc = dispatcher.get_crawler(link).extract(link)
            metadata[domain]["success"].append(link)

        except Exception as e:
            metadata[domain]["failure"].append({'url': link, "error": str(e)})


        docs.append(doc)

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="docs", metadata=metadata)

    return docs

@step
def insert_docs_to_db(docs: list[Document]):
    client = MongoDBClient()
    client.insert_many_docs(docs)

@pipeline
def insert_data_to_db_pipeline(links: list[str]):
    docs = crawl_links(links=links)
    insert_docs_to_db(docs=docs)

@pipeline
def insert_profile_data_to_db_pipeline(profile_url: str):
    links = crawl_profile(profile_url=profile_url)
    docs = crawl_links(links=links)
    insert_docs_to_db(docs=docs)
