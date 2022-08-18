from __future__ import annotations
from enum import Enum
from itertools import count
from math import sqrt
from random import randint, random
from re import compile, RegexFlag
from statistics import mean
from typing import (
    Any,
    Callable,
    Generic,
    Hashable,
    Iterable,
    Iterator,
    Literal,
    SupportsIndex,
    TypeVar,
    overload,
)

try:
    from .exceptions import *
except ImportError:
    from exceptions import *

_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_R = TypeVar("_R")
_H = TypeVar("_H", Hashable, Any)


DEFAULT_FORMAT = "<{}(, )>"
DEFAULT_REPR_FORMAT = "<{!r}(, )>"
_REGEX_STREAM_FORMAT = r"^(.*)(\{[^\\\{\}]*\})\((.*)\)(.*)$"

_streamformatmatch = compile(_REGEX_STREAM_FORMAT, flags=RegexFlag.S)


def _match_format(__format_spec: str) -> tuple[str, str, str, str]:
    match = _streamformatmatch.match(__format_spec)
    if match is None:
        raise StreamFormatError
    return match.groups()


class Len(Enum):
    INF = -1
    UNK = 0
    FIN = 1


def _next(__i: Iterable[_T]) -> _T:
    """Wrapper for python next(__i) with check for StreamExceptions"""
    nx = next(__i)
    if isinstance(nx, StreamException):
        raise nx.exc
    return nx


class Stream(Generic[_T]):
    """Class to utilize Java-like object streams in python
    Example usage:
    >>> Stream([1,2,3,4,5]) -> <1,2,3,4,5>
    >>> Stream.range(4)    -> <0,1,2,3>
    >>> Stream.primes().limit(3) -> <2,3,5>

    Stream methods can be chained.
    Evaluation is inherently lazy, only evaluating and consuming the stream when
    required. It is therefore possible to use infinite data streams.
    Some methods require the stream to be finite (such as Stream.last())
    """

    def __init__(self, __iter: Iterable[_T], length: Len = None) -> None:
        """"""
        self.__iter = __iter
        if length == None:
            try:
                len(self.__iter)
                self.__length = Len.FIN
            except TypeError:
                self.__length = Len.UNK
        else:
            self.__length = length

    # Class methods for special streams
    @overload
    @classmethod
    def range(cls, __stop: SupportsIndex, /) -> Stream[int]:
        ...

    @overload
    @classmethod
    def range(cls, __start: SupportsIndex, __stop: SupportsIndex, /) -> Stream[int]:
        ...

    @overload
    @classmethod
    def range(
        cls, __start: SupportsIndex, __stop: SupportsIndex, __step: SupportsIndex, /
    ) -> Stream[int]:
        ...

    @classmethod
    def range(cls, *args) -> Stream[int]:
        return cls(range(*args), Len.FIN)

    @overload
    @classmethod
    def counter(cls) -> Stream[int]:
        ...

    @overload
    @classmethod
    def counter(cls, start: int, _step: int) -> Stream[int]:
        ...

    @overload
    @classmethod
    def counter(cls, *, _step: int) -> Stream[int]:
        ...

    @classmethod
    def counter(cls, *args) -> Stream[int]:
        return cls(count(*args), Len.INF)

    @classmethod
    def generate(
        cls, __func: Callable[[Any], _T], args: tuple = None, kwargs: dict = None
    ) -> Stream[_T]:
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        def loop():
            while True:
                yield __func(*args, **kwargs)

        return cls(loop(), Len.INF)

    @classmethod
    def repeat(cls, __val: _T) -> Stream[_T]:
        return cls.generate(lambda: __val)

    @classmethod
    def random(cls) -> Stream[float]:
        return cls.generate(random)

    @classmethod
    def randint(cls, a: int, b: int) -> Stream[int]:
        return cls.generate(randint, (a, b))

    @classmethod
    def randbool(cls) -> Stream[bool]:
        return cls.generate(randint, (0, 1)).eval(bool)

    @classmethod
    def primes(cls) -> Stream[int]:
        def quasiprimes():
            yield 2
            yield 3
            n = 6
            while True:
                yield n - 1
                yield n + 1
                n += 6

        def isprime(n: int) -> bool:
            it = iter(quasiprimes())
            for d in it:
                if d > sqrt(n):
                    break
                if n % d == 0 and n != d:
                    return False
            return True

        def loop():
            it = quasiprimes()
            for p in it:
                if isprime(p):
                    yield p

        return cls(loop(), Len.INF)

    # Operations to limit the data items

    def filter(self, __key: Callable[[_T], bool], keep_if: bool = True) -> Stream[_T]:
        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = iter(__iter)
                while True:
                    nx = _next(it)
                    if __key(nx) == keep_if:
                        yield nx
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def slice(self, start: int = 0, stop: int = None, step: int = 1) -> Stream[_T]:
        if stop is not None:
            self.__length = Len.FIN
        if step < 1:
            raise ValueError("Step value must be 1 or greater")
        if start > stop:
            raise ValueError("Start value must be smaller than stop value")

        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = enumerate(__iter)
                while True:
                    i, nx = next(it)
                    if isinstance(nx, StreamException):
                        raise nx.exc
                    if stop is not None and i >= stop:
                        return
                    if i < start:
                        continue
                    if (i - start) % step == 0:
                        yield nx
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def skip(self, count: int) -> Stream[_T]:
        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = iter(__iter)
                for _ in range(count):
                    next(it)
                while True:
                    nx = _next(it)
                    yield nx
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def limit(self, count: int) -> Stream[_T]:
        self.__length = Len.FIN

        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = enumerate(__iter)
                while True:
                    i, nx = next(it)
                    if isinstance(nx, StreamException):
                        raise nx.exc
                    if i >= count:
                        return
                    yield nx
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def stop(self, __when: Callable[[_T], bool], inclusive: bool = False) -> Stream[_T]:
        if self.__length == Len.INF:
            self.__length = Len.UNK

        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = iter(__iter)
                while True:
                    nx = _next(it)
                    if __when(nx):
                        if inclusive:
                            yield nx
                        return
                    yield nx
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def distinct(self) -> Stream[_T]:
        if self.__length == Len.INF:
            raise UnlimitedStreamException

        def loop(__iter: Iterable[_H]) -> Iterable[_H]:
            try:
                it = iter(__iter)
                items = set()
                while True:
                    nx = _next(it)
                    if nx not in items:
                        items.add(nx)
                        yield nx
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    # Operations to change the data items

    def enumerate(self) -> Stream[_T]:
        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = enumerate(__iter)
                while True:
                    i, nx = next(it)
                    if isinstance(nx, StreamException):
                        raise nx.exc
                    yield (i, nx)
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def replace(self, __old: _T, __new: _R) -> Stream[_T | _R]:
        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = iter(__iter)
                while True:
                    nx = _next(it)
                    yield __new if nx == __old else nx
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def replace_with(
        self, __with: Callable[[_T], _R], __when: Callable[[_T], bool] = lambda _: True
    ) -> Stream[_T | _R]:
        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = iter(__iter)
                while True:
                    nx = _next(it)
                    try:
                        if __when(nx):
                            yield __with(nx)
                        else:
                            yield nx
                    except Exception as E:
                        yield StreamException(E, nx)
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def eval(self, __func: Callable[[_T], _R]) -> Stream[_R]:
        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = iter(__iter)
                while True:
                    nx = _next(it)
                    try:
                        yield __func(nx)
                    except Exception as E:
                        yield StreamException(E, nx)
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    # @overload
    # def exc(
    #     self, exc: Exception, todo: Literal["replace"], /, __with: _R
    # ) -> Stream[_T | _R]:
    #     ...

    # @overload
    # def exc(
    #     self, exc: Exception, todo: Literal["with"], /, __with: Callable[[_T], _R]
    # ) -> Stream[_T | _R]:
    #     ...

    # @overload
    # def exc(self, exc: Exception, todo: Literal["stop", "continue"], /) -> Stream[_T]:
    #     ...

    def exc(
        self,
        exc: Exception,
        todo: Literal["stop", "continue", "with", "replace"],
        /,
        __with: _R | Callable[[_T], _R] = None,
    ) -> Stream[_T | _R]:
        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = iter(__iter)
                while True:
                    nx = next(it)
                    if isinstance(nx, StreamException) and isinstance(nx.exc, exc):
                        if todo == "continue":
                            continue
                        elif todo == "replace":
                            yield __with
                        elif todo == "with":
                            try:
                                yield __with(nx.val)
                            except Exception as E:
                                yield StreamException(E, nx.val)
                        else:
                            return  # 'stop'
                    else:
                        yield nx
            except StopIteration:
                return

        self.__iter = loop(self.__iter)
        return self

    def zip(self, __other: Stream[_T1]) -> Stream[tuple[_T, _T1]]:
        self.__length = min(self.__length, __other.__length)
        self.__iter = zip(self._loop(), __other._loop())

    # Operations to consume the data items

    def _loop(self) -> Iterable[_T]:
        try:
            it = iter(self.__iter)
            while True:
                yield _next(it)
        except StopIteration:
            return

    def _loop_key(self, __key: Callable[[_T], bool] = lambda _: True) -> Iterable[_T]:
        yield from (e for e in self._loop() if __key(e))

    def list(self) -> list[_T]:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return list(self._loop())

    def tuple(self) -> tuple[_T]:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return tuple(self._loop())

    def set(self) -> set[_T]:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return set(self._loop())

    def null(self) -> None:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        try:
            it = iter(self.__iter)
            while True:
                _ = _next(it)
        except StopIteration:
            return

    def first(
        self, __key: Callable[[_T], bool] = lambda _: True, default: _T = None
    ) -> _T:
        try:
            it = iter(self._loop_key(__key))
            return next(it)
        except StopIteration:
            return default

    def last(
        self, __key: Callable[[_T], bool] = lambda _: True, default: _T = None
    ) -> _T:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        try:
            it = iter(self._loop_key(__key))
            nx = default
            while True:
                nx = next(it)
        except StopIteration:
            return nx

    def sum(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return sum(e for e in self._loop() if __key(e))

    def count(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return sum(1 for e in self._loop() if __key(e))

    def mean(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return mean(e for e in self._loop() if __key(e))

    def all(self, __func: Callable[[_T], bool] = lambda x: x) -> bool:
        return all(self._loop())

    def any(self, __func: Callable[[_T], bool] = lambda x: x) -> bool:
        return any(self._loop())

    def min(self) -> _T:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return min(self._loop())

    def max(self) -> _T:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return max(self._loop())

    def split(self, __key: Callable[[_T], _H]) -> dict[_H, Stream[_T]]:
        """The method returns a dict of streams. The streams are obtained by grouping,
        in order, all elements returning the same value when the __key function is
        applied to them. If an exception is raised by the __key function the key is
        obtained as such:
         ZeroDivisionError -> __exc_ZeroDivisionError"""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        out = {}
        out: dict[_H, list[_T]]
        for elm in self._loop():
            try:
                k = __key(elm)
            except Exception as E:
                elm = StreamException(E, elm)
                k = f"__exc_{E.__class__.__name__}"
            if k not in out:
                out[k] = list()
            out[k].append(elm)
        return {k: Stream(v) for k, v in out.items()}

    def split_list(self, __key: Callable[[_T], _H]) -> dict[_H, list[_T]]:
        """The method returns a dict of lists. The lists are obtained by grouping,
        in order, all elements returning the same value when the __key function is
        applied to them."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        out = {}
        out: dict[_H, list[_T]]
        for elm in self._loop():
            k = __key(elm)
            if k not in out:
                out[k] = list()
            out[k].append(elm)
        return out

    def __iter__(self) -> Iterator[_T]:
        return iter(self._loop())

    # Operations to output to text

    def print(self, __format_spec: str = "<{}(, )>\n") -> Stream[_T]:
        if self.__length == Len.INF:
            raise UnlimitedStreamException

        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            pre, frm, sep, end = _match_format(__format_spec)
            try:
                it = iter(__iter)
                out = pre
                nx = _next(it)
                out += frm.format(nx)
                yield nx
                while True:
                    nx = _next(it)
                    out += sep + frm.format(nx)
                    yield nx
            except StopIteration:
                out += end
                print(out)
                return
            except GeneratorExit:
                out += sep + "..." + end
                print(out)
                return

        self.__iter = loop(self.__iter)
        return self

    def __format__(self, __format_spec: str) -> str:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        if __format_spec == "":
            __format_spec = DEFAULT_FORMAT
        pre, frm, sep, end = _match_format(__format_spec)
        return f"{pre}{sep.join(frm.format(e) for e in self)}{end}"

    def __repr__(self) -> str:
        return self.__format__(DEFAULT_REPR_FORMAT)

    def __str__(self) -> str:
        return self.__format__(DEFAULT_FORMAT)

    # Miscellaneous

    def _length_override(self, length: Len) -> Stream[_T]:
        self.__length = length
        return self

    def cache(
        self, list_cache: list[_T], _copy_method: Callable[[list], list] = None
    ) -> Stream[_T]:
        """The method consumes the stream and stores it into a list which reference
        is passed to list_cache. The list is first cleared with the list.clear()
        method, and the stream returned uses a shallow copy of the list. To use a
        deep copy you can change the _copy_method of the function (default: list.copy)."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        if _copy_method is None:
            _copy_method = list.copy
        list_cache.clear()
        list_cache.extend(self.__iter)
        self.__iter = _copy_method(list_cache)
        return self
