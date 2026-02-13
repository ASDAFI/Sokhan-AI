from sokhan.data_entry.domain.tasnim.crawlers import TasnimHomePageCrawler
from sokhan.data_entry.pipelines import insert_data_to_db_pipeline_async

if __name__ == "__main__":
    tsnm = TasnimHomePageCrawler()
    for batch in tsnm.extract(url="https://tasnimnews.ir/fa/top-stories",
                              min_date="1404-06-01 00:01",
                              max_clicks=100000):
        insert_data_to_db_pipeline_async(links=batch)
