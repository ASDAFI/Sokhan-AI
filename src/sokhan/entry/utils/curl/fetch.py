from io import BytesIO
from urllib.parse import urlparse, quote, urlunparse
from typing import Optional, Union, Dict
import json
from functools import wraps

import pycurl

from sokhan.entry.utils.curl.configs import *
from sokhan.entry.utils.curl.exceptions import *



class PyCurlAgent:
    def __init__(self) -> None:
        self.response_buffer: BytesIO = BytesIO()
        self.header_buffer: BytesIO = BytesIO()
        self.pycurl_obj: pycurl.Curl = pycurl.Curl()

    @staticmethod
    def encode_url(url: str, change_schema_to_http: bool = False) -> str:
        parsed_url = urlparse(url)
        scheme = 'http' if change_schema_to_http else quote(parsed_url.scheme)
        return urlunparse((
            scheme,
            parsed_url.netloc,
            quote(parsed_url.path),
            quote(parsed_url.params),
            quote(parsed_url.query),
            quote(parsed_url.fragment)
        ))

    def _validate_inputs(self, request_type: str, post_data: dict) -> None:
        if request_type not in ["GET", "POST"]:
            raise ValueError("request_type must be 'GET' or 'POST'")

        if post_data is not None and request_type != "POST":
            raise ValueError("post_data can only be used with POST requests")

    def _apply_request_type(
            self,
            request_type: str,
            post_data: Optional[dict],
            headers: Dict[str, str]
    ) -> None:

        if request_type == "POST":
            self.pycurl_obj.setopt(pycurl.POST, 1)

            if post_data:
                post_json = json.dumps(post_data)
                self.pycurl_obj.setopt(pycurl.POSTFIELDS, post_json)
                headers["Content-Type"] = "application/json"
            else:
                self.pycurl_obj.setopt(pycurl.POSTFIELDS, "")

    def _apply_max_file_size(self, max_file_size: Optional[int]) -> None:
        if max_file_size is None:
            return

        self.pycurl_obj.setopt(pycurl.MAXFILESIZE, max_file_size)
        self.pycurl_obj.setopt(pycurl.RANGE, f"0-{max_file_size - 1}")

    def _apply_basic_options(
            self,
            url: str,
            timeout: int,
            user_agents: str,
            change_schema_to_http: bool
    ) -> None:

        self.pycurl_obj.setopt(pycurl.FOLLOWLOCATION, True)
        self.pycurl_obj.setopt(pycurl.OPT_CERTINFO, 1)

        self.pycurl_obj.setopt(pycurl.WRITEDATA, self.response_buffer)
        self.pycurl_obj.setopt(pycurl.HEADERFUNCTION, self.header_buffer.write)

        encoded_url = self.encode_url(url, change_schema_to_http)
        self.pycurl_obj.setopt(pycurl.URL, encoded_url)

        self.pycurl_obj.setopt(pycurl.USERAGENT, user_agents)
        self.pycurl_obj.setopt(pycurl.CONNECTTIMEOUT, timeout)
        self.pycurl_obj.setopt(pycurl.TIMEOUT, FETCH_TIMEOUT)

        self.pycurl_obj.setopt(pycurl.ACCEPT_ENCODING, "gzip, deflate, br")
        self.pycurl_obj.setopt(pycurl.MAXREDIRS, 10)

    def _apply_http_version(self, http11: bool, http09: bool) -> None:
        if http11:
            self.pycurl_obj.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
        elif http09:
            self.pycurl_obj.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_NONE)

    def _apply_tls_settings(
            self,
            verify: bool,
            cert_file: Optional[str],
            tls1: bool
    ) -> None:

        if tls1:
            self.pycurl_obj.setopt(pycurl.SSLVERSION, pycurl.SSLVERSION_TLSv1_0)

        if not verify:
            self.pycurl_obj.setopt(pycurl.SSL_VERIFYPEER, 0)
            self.pycurl_obj.setopt(pycurl.SSL_VERIFYHOST, 0)
            return

        self.pycurl_obj.setopt(pycurl.SSL_VERIFYPEER, 1)
        self.pycurl_obj.setopt(pycurl.SSL_VERIFYHOST, 2)

        if cert_file:
            self.pycurl_obj.setopt(pycurl.CAINFO, cert_file)

    def apply_headers(self, headers: Dict[str, str]) -> None:
        if not headers:
            return

        formatted = [f"{k}: {v}" for k, v in headers.items()]
        self.pycurl_obj.setopt(pycurl.HTTPHEADER, formatted)

    def set_default_options(
            self,
            request_type: str,
            url: str,
            timeout: int = FETCH_TIMEOUT,
            post_data: dict = None,
            verify: bool = False,
            user_agents: str = "",
            http11: bool = False,
            http09: bool = False,
            tls1: bool = False,
            max_file_size: Optional[int] = None,
            change_schema_to_http: bool = False,
            headers: Optional[Dict[str, str]] = None,
            cert_file: Optional[str] = None
    ) -> None:
        self._validate_inputs(request_type, post_data)

        headers = headers or {}

        self._apply_request_type(request_type, post_data, headers)
        self._apply_max_file_size(max_file_size)
        self._apply_basic_options(url, timeout, user_agents, change_schema_to_http)
        self.apply_headers(headers)
        self._apply_http_version(http11, http09)
        self._apply_tls_settings(verify, cert_file, tls1)

    @staticmethod
    def decode_buffer(buffer: BytesIO) -> str:
        try:
            return buffer.getvalue().decode("utf-8")
        except UnicodeDecodeError:
            return buffer.getvalue().decode("iso-8859-1")

    def setopt(self, option: int, value: Union[int, str, BytesIO]) -> None:
        self.pycurl_obj.setopt(option, value)

    def getinfo(self, item: int) -> Union[int, str, float]:
        return self.pycurl_obj.getinfo(item)

    def get_content(self) -> BytesIO:
        return self.response_buffer

    def get_header(self) -> BytesIO:
        return self.header_buffer

    def get_decoded_content(self) -> str:
        return self.decode_buffer(self.get_content())

    def get_decoded_header(self) -> str:
        return self.decode_buffer(self.get_header())

    @staticmethod
    def parse_headers(raw_headers: str) -> Dict[str, str]:
        headers = {}
        for line in raw_headers.splitlines():
            line = line.strip()
            if not line or ":" not in line or line.startswith("HTTP/"):
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in headers:
                if isinstance(headers[key], list):
                    headers[key].append(value)
                else:
                    headers[key] = [headers[key], value]
            else:
                headers[key] = value
        return headers

    def get_json_headers(self) -> dict[str, str]:
        headers_raw = self.get_decoded_header()
        headers = self.parse_headers(headers_raw)

        return headers

    def perform(self) -> None:
        try:
            self.pycurl_obj.perform()
        except pycurl.error as e:
            error_code, error_msg = e.args
            if error_code in (pycurl.MAXFILESIZE, pycurl.E_FILESIZE_EXCEEDED):
                raise SizeLimitException("Size limit exceeded.")
            elif "HTTP/2" in error_msg or (error_code == pycurl.E_RECV_ERROR and "large response" in error_msg):
                raise HTTP2Exception("HTTP/2 not valid version.")
            elif error_code == pycurl.E_UNSUPPORTED_PROTOCOL and "HTTP/0.9 when not allowed" in error_msg:
                raise HTTP09Exception("HTTP/0.9 not valid version.")
            elif error_code in (pycurl.E_SSL_CONNECT_ERROR, pycurl.E_RECV_ERROR) and "SSL" in error_msg:
                raise SSLException(error_msg)
            elif error_code in (pycurl.E_COULDNT_RESOLVE_HOST, 97) and "Could not resolve host" in error_msg:
                raise HostResolutionException("Could not resolve host.")
            elif error_code == pycurl.E_OPERATION_TIMEDOUT:
                raise TimeoutException("Request timeout.")
            elif error_code == pycurl.E_GOT_NOTHING:
                raise EmptyReplyException("Empty reply from server.")
            else:
                raise

    def get_content_type(self) -> Optional[str]:
        return self.pycurl_obj.getinfo(pycurl.CONTENT_TYPE)

    def get_json_content(self):
        response_data = json.loads(self.get_decoded_content())
        return response_data

    def get_response_code(self):
        return self.getinfo(pycurl.RESPONSE_CODE)

    def close(self) -> None:
        self.pycurl_obj.close()
        self.response_buffer.close()
        self.header_buffer.close()


def handle_with_pycurl(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = PyCurlAgent()
        try:
            return func(*args, session=session, **kwargs)
        finally:
            session.close()

    return wrapper
