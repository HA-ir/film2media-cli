"""
Standard exception hierarchy for film2media-cli.
"""


class F2MError(Exception):
    """Base exception for all film2media domain errors."""
    pass


class F2MConfigError(F2MError):
    """Raised when configuration validation, parsing, or saving fails."""
    pass


class F2MNetworkError(F2MError):
    """Raised when network transport or site communication fails."""
    pass


class F2MParseError(F2MError):
    """Raised when markup, response, or entity parsing fails."""
    pass
