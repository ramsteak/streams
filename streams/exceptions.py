from typing import TypeVar


_T = TypeVar("_T")


class StreamException:
    """Container class to catch and transport exceptions without raising them
    immediately, which would interrupt the stream.
    This class should not be used in any way outside of streams exception handling."""

    def __init__(self, exc: Exception, val: _T) -> None:
        self.exc, self.val = exc, val

    def __str__(self) -> str:
        return str(self.exc)


class StreamFormatError(Exception):
    """Raised if the stream format does not follow the pattern"""


class UnlimitedStreamException(Exception):
    """Raised by some methods that would hang given an infinite stream (cache,
    reverse, last, ...)"""
