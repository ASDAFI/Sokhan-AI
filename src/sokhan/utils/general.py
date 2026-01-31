from urllib.parse import urlparse

from pydantic import AnyUrl


def get_domain(url: AnyUrl) -> AnyUrl:
    return urlparse(url).netloc
