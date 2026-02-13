from typing import Annotated

from pydantic import AnyUrl, Field

from sokhan.data_entry.base.documents import Document

FilePath = Annotated[str, "filesystem path"]
CodeContent = Annotated[str, "code content"]


class GitRepositoryDocument(Document):
    path_map_content: dict[FilePath, CodeContent] = Field(default_factory=dict)
    repo_path: AnyUrl
    repo_name: str

    @property
    def collection_name(self):
        return "repository"
