from typing import TypeVar


_T = TypeVar("_T")


class StreamException:
    def __init__(self, exc: Exception, val: _T) -> None:
        self.exc, self.val = exc, val

    def __str__(self) -> str:
        return str(self.exc)


class StreamFormatError(Exception):
    ...


class UnlimitedStreamException(Exception):
    ...
