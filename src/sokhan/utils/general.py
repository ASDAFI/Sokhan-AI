import datetime
from urllib.parse import urlparse

import jdatetime
from pydantic import AnyUrl


def get_domain(url: AnyUrl) -> AnyUrl:
    return urlparse(url).netloc


def from_jalali_to_gregorian(year: int, month: int, day: int) -> datetime.datetime:
    j_date = jdatetime.date(year, month, day)
    g_date = j_date.togregorian()

    return g_date
