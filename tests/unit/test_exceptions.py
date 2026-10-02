import pytest
from f2m.core.exceptions import (
    F2MError,
    F2MConfigError,
    F2MNetworkError,
    F2MParseError,
)


def test_exception_hierarchy():
    assert issubclass(F2MConfigError, F2MError)
    assert issubclass(F2MNetworkError, F2MError)
    assert issubclass(F2MParseError, F2MError)
    assert issubclass(F2MError, Exception)


def test_exception_instantiation():
    err = F2MConfigError("Invalid player: invalid_player")
    assert str(err) == "Invalid player: invalid_player"
    assert isinstance(err, F2MError)
