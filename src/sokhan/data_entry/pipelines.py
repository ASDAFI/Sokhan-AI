import itertools
from collections import defaultdict

from typing import Annotated
from zenml import get_step_context, step, pipeline

from sokhan.utils.db.mongo_client import MONGO_CLIENT
from sokhan.data_entry.base.documents import Document
from sokhan.data_entry.crawlers import CrawlerDispatcher, ProfileCrawlerDispatcher, FeedCrawlerDispatcher
from sokhan.utils.general import get_domain


@step(enable_cache=False)
def crawl_profile(profile_url: str) -> Annotated[list[str], "links"]:
    dispatcher = ProfileCrawlerDispatcher().create_default()
    links = dispatcher.get_crawler(profile_url).extract(profile_url)

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="links", metadata={"links": links})

    return links


@step(enable_cache=False)
def crawl_links_async(links: list[str]) -> Annotated[list[Document], "docs"]:
    dispatcher = CrawlerDispatcher.create_default()
    metadata = defaultdict(lambda: {"success": [], "failure": []})

    docs = []

    domain_map_links = defaultdict(list)

    for link in links:
        domain = get_domain(link)
        domain_map_links[domain].append(link)

    for domain, links in domain_map_links.items():
        # TODO: Fix success/failure per link
        try:
            domain_docs = dispatcher.get_crawler(links[0]).extract_urls(links)
            docs.extend(domain_docs)
            metadata[domain]["success"] = links

        except:
            metadata[domain]["failure"] = links

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="docs", metadata=metadata)

    return docs


@step(enable_cache=False)
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


@step(enable_cache=False)
def bulk_insert_docs_to_db(docs: list[Document]):
    coll_map_docs = defaultdict(list)

    for doc in docs:
        coll_map_docs[doc.collection_name].append(doc)

    for collection_name, grouped_docs in coll_map_docs.items():
        MONGO_CLIENT.bulk_insert(collection_name,
                                 [doc.to_mongo_dict() for doc in grouped_docs]
                                 )


@step(enable_cache=False)
def load_feeds(feed_url: str, min_date: str) -> Annotated[list[str], "news_urls"]:
    dispatcher = FeedCrawlerDispatcher.create_default()

    news_urls = list(itertools.chain.from_iterable(
        dispatcher.get_crawler(feed_url).extract(feed_url, min_date=min_date)
    ))
    metadata = {"urls_count": len(news_urls), "found_urls": news_urls}

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="news_urls", metadata=metadata)

    return news_urls


@pipeline
def insert_data_to_db_pipeline(links: list[str]):
    docs = crawl_links(links=links)
    bulk_insert_docs_to_db(docs=docs)


@pipeline
def insert_data_to_db_pipeline_async(links: list[str]):
    docs = crawl_links_async(links=links)
    bulk_insert_docs_to_db(docs=docs)


@pipeline
def insert_profile_data_to_db_pipeline(profile_url: str):
    links = crawl_profile(profile_url=profile_url)
    docs = crawl_links(links=links)
    bulk_insert_docs_to_db(docs=docs)


@pipeline
def insert_profile_data_to_db_pipeline_async(profile_url: str):
    links = crawl_profile(profile_url=profile_url)
    docs = crawl_links_async(links=links)
    bulk_insert_docs_to_db(docs=docs)


@pipeline
def insert_small_feed_to_db_pipeline_async(feed_url: str, min_date="1404-11-23 00:00"):
    news_urls = load_feeds(feed_url=feed_url, min_date=min_date)
    docs = crawl_links_async(links=news_urls)
    bulk_insert_docs_to_db(docs=docs)
