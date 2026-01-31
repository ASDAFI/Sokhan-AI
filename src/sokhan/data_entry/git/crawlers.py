import tempfile
import os
import shutil

import git
from pydantic import AnyUrl
from loguru import logger

from sokhan.data_entry.git.documents import GitRepositoryDocument
from sokhan.data_entry.base.crawlers import BaseCrawler


def is_ignore(filename: str, ignores: list[str]) -> bool:
    for name in filename.split("/"):
        for ignore in ignores:
            if name.endswith(ignore):
                return True
    return False

def read_content(filename: str) -> str:
    with open(filename, "r") as f:
        return f.read()

class GitCrawler(BaseCrawler):
    def extract(self, url: AnyUrl, ignore=[".git", ".toml", ".lock", ".png", ".jpg"]) -> GitRepositoryDocument:
        local_tmp = tempfile.mkdtemp()

        try:
            git.Git(local_tmp).clone(url)

            repo_name = os.listdir(local_tmp)[0]

            path_map_content = {}

            for root, dirs, files in os.walk(local_tmp):
                relative_root = root.replace(os.path.join(local_tmp, repo_name), '')

                for file in files:
                    relative_path = os.path.join(relative_root, file)
                    real_path = os.path.join(root, file)

                    if not is_ignore(relative_path, ignore):
                        try:
                            path_map_content[relative_path] = read_content(real_path)
                        except Exception as e:
                            logger.warning(f"Cant Read file {relative_path} from repo {url}", e)

            doc = GitRepositoryDocument(repo_path=url, repo_name=repo_name, path_map_content=path_map_content)

        finally:
            shutil.rmtree(local_tmp)

        return doc
