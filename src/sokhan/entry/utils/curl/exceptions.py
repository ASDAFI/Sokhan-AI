class HostResolutionException(Exception):
    error_code = 1001


class SizeLimitException(Exception):
    error_code = 1002


class HTTP2Exception(Exception):
    error_code = 1003


class HTTP09Exception(Exception):
    error_code = 1004


class ProxyException(Exception):
    error_code = 1006


class TimeoutException(Exception):
    error_code = 1007


class SSLException(Exception):
    error_code = 1009


class EmptyReplyException(Exception):
    error_code = 1010
