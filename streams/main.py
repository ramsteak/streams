from __future__ import annotations
from enum import Enum
from itertools import count, zip_longest
from math import sqrt
from random import randint, random, shuffle
from re import compile, RegexFlag
from statistics import mean
from typing import (
    Any,
    Callable,
    Generator,
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
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T4 = TypeVar("_T4")
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

    def __lt__(self: Len, __other: Len) -> bool:
        if self.__class__ is __other.__class__:
            return self.value < __other.value


def min_length(*streams: Stream[Any]) -> Len:
    """Returns the minimun Len enum for the given streams."""
    # -1 is infinite, so min() -> maximum, max() -> minimum
    return max(stream.length for stream in streams)


def max_length(*streams: Stream[Any]) -> Len:
    """Returns the maximum Len enum for the given streams."""
    return min(stream.length for stream in streams)


# def _next(__i: Iterable[_T]) -> _T:
#     """Wrapper for python next(__i) with check for StreamExceptions."""
#     nx = next(__i)
#     if isinstance(nx, StreamException):
#         raise nx.exc
#     return nx
def _loop_enter(__i: Generator[_T, None, None]) -> Generator[_T, None, None]:
    for nx in __i:
        if isinstance(nx, StreamException):
            raise nx.exc
        yield nx


def _loop(__i: Generator[_T, None, None]) -> Generator[_T, None, None]:
    try:
        for nx in __i:
            if isinstance(nx, StreamException):
                raise nx.exc
            yield nx
    except GeneratorExit:
        __i.close()
        return


def _loop_enum(__i: Generator[_T, None, None]) -> Generator[tuple[int, _T], None, None]:
    try:
        for i, nx in enumerate(__i):
            if isinstance(nx, StreamException):
                raise nx.exc
            yield i, nx
    except GeneratorExit:
        __i.close()
        return


class Stream(Generic[_T]):
    """Class to utilize Java-like object streams in python.
    Example usage:
    >>> Stream([1,2,3,4,5]) -> <1,2,3,4,5>
    >>> Stream.range(4)    -> <0,1,2,3>
    >>> Stream.primes().limit(3) -> <2,3,5>

    Stream methods can be chained.
    Evaluation is inherently lazy, only evaluating and consuming the stream when
    required. It is therefore possible to use infinite data streams.
    Some methods require the stream to be finite (such as Stream.last())."""

    def __init__(self, __iter: Iterable[_T], length: Len = None) -> None:
        """The method generates a stream object from any iterable, consuming it
        lazily when needed. The length parameter is to be set when the length
        cannot be determined automatically (such as iterables without a __len__
        method or methods where calling __len__ would consume them). Whenever
        possible it is preferrable to use the default generators, such as range
        and count.

        >>> Stream([1,2,3,4,5]) -> <1,2,3,4,5>
        >>> Stream.range(4)    -> <0,1,2,3>
        >>> Stream.primes().limit(3) -> <2,3,5>"""

        self.__iter = _loop_enter(__iter)
        if length is None:
            try:
                len(__iter)
                self.__length = Len.FIN
            except TypeError:
                self.__length = Len.UNK
        else:
            self.__length = length

    @property
    def length(self) -> Len:
        return self.__length

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
        cls,
        __start: SupportsIndex,
        __stop: SupportsIndex,
        __step: SupportsIndex,
        /,
    ) -> Stream[int]:
        ...

    @classmethod
    def range(cls, *args) -> Stream[int]:
        """The method generates a stream from the python range class. It uses
        the same arguments of the range object in standard python."""
        return cls(range(*args), Len.FIN)

    @overload
    @classmethod
    def counter(cls) -> Stream[int]:
        ...

    @overload
    @classmethod
    def counter(cls, start: int) -> Stream[int]:
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
        """The method generates an infinite counting stream using the count object
        from itertools, using the same arguments."""
        return cls(count(*args), Len.INF)

    @classmethod
    def generate(
        cls, __func: Callable[[Any], _T], args: tuple = None, kwargs: dict = None
    ) -> Stream[_T]:
        """The methods evaluates the passed function every time in order to generate
        the stream. Arguments to the function can be passed via args and kwargs."""
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
        """The method generates an infinite stream repeating the same object."""
        return cls.generate(lambda: __val)

    @classmethod
    def random(cls) -> Stream[float]:
        """The method generates an infinite stream of random values between 0 and
        1 evaluated via the random.random method."""
        return cls.generate(random)

    @classmethod
    def randint(cls, a: int, b: int) -> Stream[int]:
        """The method generates an infinite stream of random integers between a
        and b with the randint function."""
        return cls.generate(randint, (a, b))

    @classmethod
    def randbool(cls) -> Stream[bool]:
        """The method generates an infinite stream of random bools."""
        return cls.generate(randint, (0, 1)).eval(bool)

    @classmethod
    def primes(cls) -> Stream[int]:
        """The method generates an infinite stream of primes. The main focus of
        the function is not storing the values to memory, relying on a partially
        optimized method to generate and evaluating primes on the fly. It might be
        slow for very large numbers."""

        def quasiprimes():
            """The method partially optimizes the prime search because primes can
            only be one greater or one smaller than 6. Therefore it is much faster
            than checking every number or every second number."""
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

    @classmethod
    def fibonacci(cls) -> Stream[int]:
        def loop():
            a, b = 0, 1
            while True:
                yield a
                a, b = b, a + b

        return cls(loop(), Len.INF)

    @classmethod
    def empty(cls) -> Stream:
        """The method generates an empty stream."""
        return cls([], Len.FIN)

    # Class methods to operate with streams

    @overload
    @classmethod
    def zip(cls, stream: Stream[_T], strict: bool = False) -> Stream[tuple[_T]]:
        ...

    @overload
    @classmethod
    def zip(
        cls, stream: Stream[_T], stream1: Stream[_T1], strict: bool = False
    ) -> Stream[tuple[_T, _T1]]:
        ...

    @overload
    @classmethod
    def zip(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        strict: bool = False,
    ) -> Stream[tuple[_T, _T1, _T2]]:
        ...

    @overload
    @classmethod
    def zip(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        strict: bool = False,
    ) -> Stream[tuple[_T, _T1, _T2, _T3]]:
        ...

    @overload
    @classmethod
    def zip(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        stream4: Stream[_T4],
        strict: bool = False,
    ) -> Stream[tuple[_T, _T1, _T2, _T3, _T4]]:
        ...

    @overload
    @classmethod
    def zip(cls, *streams: Stream[_T], strict: bool = False) -> Stream[_T]:
        ...

    @classmethod
    def zip(cls, *streams: Stream[_T], strict: bool = False) -> Stream[_T]:
        """The method joins multiple streams with the zip python method, returning
        a new stream of tuples. The stream ends when the first stream ends.
        If strict is set then ValueError is raised if one stream ends before the others."""
        return cls(zip(*streams, strict=strict), min_length(*streams))

    @overload
    @classmethod
    def zip_longest(
        cls, stream: Stream[_T], fillvalue: _R = None
    ) -> Stream[tuple[_T | _R]]:
        ...

    @overload
    @classmethod
    def zip_longest(
        cls, stream: Stream[_T], stream1: Stream[_T1], fillvalue: _R = None
    ) -> Stream[tuple[_T | _R, _T1 | _R]]:
        ...

    @overload
    @classmethod
    def zip_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        fillvalue: _R = None,
    ) -> Stream[tuple[_T | _R, _T1 | _R, _T2 | _R]]:
        ...

    @overload
    @classmethod
    def zip_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        fillvalue: _R = None,
    ) -> Stream[tuple[_T | _R, _T1 | _R, _T2 | _R, _T3 | _R]]:
        ...

    @overload
    @classmethod
    def zip_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        stream4: Stream[_T4],
        fillvalue: _R = None,
    ) -> Stream[tuple[_T | _R, _T1 | _R, _T2 | _R, _T3 | _R, _T4 | _R]]:
        ...

    @overload
    @classmethod
    def zip_longest(cls, *streams: Stream[_T], fillvalue: _R = None) -> Stream[_T | _R]:
        ...

    @classmethod
    def zip_longest(cls, *streams: Stream[_T], fillvalue: _R = None) -> Stream[_T | _R]:
        """The method joins multiple streams with the zip_longest python method,
        returning a new stream of tuples. The stream ends when the last stream ends.
        Streams that end first are continued with fillvalue."""
        return cls(zip_longest(*streams, fillvalue=fillvalue), max_length(*streams))

    @overload
    @classmethod
    def round_robin(cls, stream: Stream[_T], *, strict: bool = False) -> Stream[_T]:
        ...

    @overload
    @classmethod
    def round_robin(
        cls, stream: Stream[_T], stream1: Stream[_T1], *, strict: bool = False
    ) -> Stream[_T | _T1]:
        ...

    @overload
    @classmethod
    def round_robin(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        *,
        strict: bool = False,
    ) -> Stream[_T | _T1 | _T2]:
        ...

    @overload
    @classmethod
    def round_robin(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        *,
        strict: bool = False,
    ) -> Stream[_T | _T1 | _T2 | _T3]:
        ...

    @overload
    @classmethod
    def round_robin(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        stream4: Stream[_T4],
        *,
        strict: bool = False,
    ) -> Stream[_T | _T1 | _T2 | _T3 | _T4]:
        ...

    @overload
    @classmethod
    def round_robin(cls, *streams: Stream[_T], strict: bool = False) -> Stream[_T]:
        ...

    @classmethod
    def round_robin(cls, *streams: Stream[_T], strict: bool = False) -> Stream[_T]:
        """The method interlaces multiple streams in an alternating fashion, stopping
        when the first stream is exhausted. If strict is set then ValueError is raised
        if one stream ends before the others."""

        def loop(*streams: Stream[_T]) -> Stream[_T]:
            for values in zip(*streams, strict=strict):
                yield from values

        return cls(loop(*streams), min_length(*streams))

    NoFillValue = object()

    @overload
    @classmethod
    def round_robin_longest(
        cls, stream: Stream[_T], *, fillvalue: _R
    ) -> Stream[_T | _R]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls, stream: Stream[_T], stream1: Stream[_T1], *, fillvalue: _R
    ) -> Stream[_T | _T1 | _R]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        *,
        fillvalue: _R,
    ) -> Stream[_T | _T1 | _T2 | _R]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        *,
        fillvalue: _R,
    ) -> Stream[_T | _T1 | _T2 | _T3 | _R]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        stream4: Stream[_T4],
        *,
        fillvalue: _R,
    ) -> Stream[_T | _T1 | _T2 | _T3 | _T4 | _R]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls, *streams: Stream[_T], fillvalue: _R
    ) -> Stream[_T | _R]:
        ...

    @overload
    @classmethod
    def round_robin_longest(cls, stream: Stream[_T]) -> Stream[_T]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls, stream: Stream[_T], stream1: Stream[_T1]
    ) -> Stream[_T | _T1]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls, stream: Stream[_T], stream1: Stream[_T1], stream2: Stream[_T2]
    ) -> Stream[_T | _T1 | _T2]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
    ) -> Stream[_T | _T1 | _T2 | _T3]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        stream4: Stream[_T4],
    ) -> Stream[_T | _T1 | _T2 | _T3 | _T4]:
        ...

    @overload
    @classmethod
    def round_robin_longest(cls, *streams: Stream[_T]) -> Stream[_T]:
        ...

    @classmethod
    def round_robin_longest(
        cls, *streams: Stream[_T], fillvalue=NoFillValue
    ) -> Stream[_T]:
        """The method interlaces multiple streams in an alternating fashion, stopping
        when the last stream is exhausted. fillvalue can be set to any value. If
        left at the default no fillvalue is returned, yielding a stream containing
        only the values of the original streams."""

        def loop(*streams: Stream[_T]) -> Iterable[_T]:
            for values in zip_longest(*streams, fillvalue=fillvalue):
                yield from values

        return cls(
            (e for e in loop(*streams) if e is not Stream.NoFillValue),
            max_length(*streams),
        )

    @overload
    @classmethod
    def chain(cls, stream: Stream[_T]) -> Stream[_T]:
        ...

    @overload
    @classmethod
    def chain(cls, stream: Stream[_T], stream1: Stream[_T1]) -> Stream[_T | _T1]:
        ...

    @overload
    @classmethod
    def chain(
        cls, stream: Stream[_T], stream1: Stream[_T1], stream2: Stream[_T2]
    ) -> Stream[_T | _T1 | _T2]:
        ...

    @overload
    @classmethod
    def chain(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
    ) -> Stream[_T | _T1 | _T2 | _T3]:
        ...

    @overload
    @classmethod
    def chain(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
        stream4: Stream[_T4],
    ) -> Stream[_T | _T1 | _T2 | _T3 | _T4]:
        ...

    @overload
    @classmethod
    def chain(cls, *streams: Stream[_T]) -> Stream[_T]:
        ...

    @classmethod
    def chain(cls, *streams: Stream[_T]) -> Stream[_T]:
        """The method conc"""
        if any(stream.length == Len.INF for stream in streams[:-1]):
            raise UnlimitedStreamException

        def loop(*streams: Stream[_T]) -> Iterable[_T]:
            for stream in streams:
                yield from stream

        return cls(loop(*streams), max_length(*streams))

    @classmethod
    def operate(
        cls,
        operator: Callable[[_T, _T], _R],
        *streams: Stream[_T],
        strict: bool = False,
    ) -> Stream[_R]:
        """The method operates between the elements of multiple streams with the
        operator function. The elements are passed to the operator individually.
        Note: to use functions such as sum, which expects an iterable, use operate_iter."""
        return Stream.zip(*streams, strict=strict).eval(lambda x: operator(*x))

    @classmethod
    def operate_iter(
        cls,
        operator: Callable[[_T, _T], _R],
        *streams: Stream[_T],
        strict: bool = False,
    ) -> Stream[_R]:
        """The method operates between the elements of multiple streams with the
        operator function. The elements are passed to the operator as a tuple."""
        return Stream.zip(*streams, strict=strict).eval(lambda x: operator(x))

    # Operations to limit the data items

    def filter(
        self,
        __key: Callable[[_T], bool],
        /,
        *,
        keep_if: bool = True,
        exceptions: Literal["keep", "discard", "raise", "stop"] = "raise",
    ) -> Stream[_T]:
        """The method iterates through the stream evaluating each element via the
        __key function. All values which do not return the same value as keep_if
        are discarded."""

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for elm in _loop(__iter):
                    try:
                        if __key(elm) == keep_if:
                            yield elm
                    except Exception as E:
                        match exceptions:
                            case "keep":
                                yield elm
                            case "discard":
                                continue
                            case "raise":
                                raise E
                            case "stop":
                                __iter.close()
                                return
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def slice(self, start: int = 0, stop: int = None, step: int = 1) -> Stream[_T]:
        """The method allows to select a slice of the stream via the start, stop,
        step parameters."""
        if stop is not None:
            self.__length = Len.FIN
        if step < 1:
            raise ValueError("Step value must be 1 or greater")
        if start > stop:
            raise ValueError("Start value must be smaller than stop value")

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for i, elm in _loop_enum(__iter):
                    if stop is not None and i >= stop:
                        __iter.close()
                        return
                    if i < start:
                        # TODO: generator.send to skip elements -> .print() -> '<..., 3, 4, ...>
                        continue
                    if (i - start) % step == 0:
                        yield elm
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def skip(self, count: int) -> Stream[_T]:
        """The method allows to skip a number of items, resuming the stream after
        the specified amount."""

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for i, elm in _loop_enum(__iter):
                    if i < count:
                        # TODO: generator.send to skip elements -> .print() -> '<..., 3, 4, ...>
                        continue
                    yield elm
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def limit(self, count: int) -> Stream[_T]:
        """The method cuts the stream after the specified amount of item is yielded."""
        self.__length = Len.FIN

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for i, elm in _loop_enum(__iter):
                    yield elm
                    if i >= count - 1:  # -1 necessary to not consume another element
                        __iter.close()
                        return
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def stop(
        self,
        __when: Callable[[_T], bool],
        /,
        *,
        inclusive: bool = False,
        exceptions: Literal["keep", "discard", "raise", "stop"] = "raise",
    ) -> Stream[_T]:
        """The method stops the stream when the __when function evaluates to true.
        If set to true, the inclusive parameter prints the element that evaluated
        to true before interrupting the stream."""
        if self.__length == Len.INF:
            self.__length = Len.UNK

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for elm in _loop(__iter):
                    try:
                        if __when(elm):
                            if inclusive:
                                yield elm
                            __iter.close()
                            return
                        yield elm
                    except Exception as E:
                        match exceptions:
                            case "keep":
                                yield elm
                            case "discard":
                                continue
                            case "raise":
                                raise E
                            case "stop":
                                if inclusive:
                                    yield elm
                                __iter.close()
                                return
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def distinct(self) -> Stream[_T]:
        """The method removes all elements that repeat in the stream. It is to be
        noted that it uses a set to cache the elements, therefore the elements must
        be hashable."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                items = set()
                for elm in _loop(__iter):
                    if elm not in items:
                        items.add(elm)
                        yield elm
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    # Operations to change the data items

    def enumerate(self) -> Stream[_T]:
        """The mehtod functions in the same way that the enumerate object functions
        in normal python, by yielding tuples in the form of (index, value)."""

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                yield from _loop_enum(__iter)
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def replace(self, __old: _T, __new: _R) -> Stream[_T | _R]:
        """The method replaces every instance of __old with __new."""

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for elm in _loop(__iter):
                    if elm == __old:
                        yield __new
                    else:
                        yield elm
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def replace_with(
        self,
        __with: Callable[[_T], _R],
        /,
        __when: Callable[[_T], bool] = lambda _: True,
        *,
        exceptions: Literal["keep", "discard", "raise", "stop"] = "keep",
    ) -> Stream[_T | _R]:
        """The method replaces every element with the output of the __with function.
        If set, the __when function determines whether or not to change the element.
        Exceptions thrown by either __with or __when are caught as StreamException,
        and can be dealt with in a subsequent .exc method. Any exception that is not
        caught in this way is raised in any subsequent method."""

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for elm in _loop(__iter):
                    try:
                        if __when(elm):
                            yield __with(elm)
                        else:
                            yield elm
                    except Exception as E:
                        match exceptions:
                            case "keep":
                                yield StreamException(E, elm)
                            case "discard":
                                continue
                            case "raise":
                                raise E
                            case "stop":
                                __iter.close()
                                return
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def eval(
        self,
        __func: Callable[[_T], _R],
        /,
        *,
        exceptions: Literal["keep", "discard", "raise", "stop"] = "keep",
    ) -> Stream[_R]:
        """The method replaces every element of the stream with the output of the
        __func function.
        Exceptions thrown by __func are caught as StreamException, and can be dealt
        with in a subsequent .exc method. Any exception that is not caught in this
        way is raised in any subsequent method.
        In order to catch BaseExceptions you can call the _eval method, but it is
        not recommended to use it except in specific circumstances."""

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for elm in _loop(__iter):
                    try:
                        yield __func(elm)
                    except Exception as E:
                        match exceptions:
                            case "keep":
                                yield StreamException(E, elm)
                            case "discard":
                                continue
                            case "raise":
                                raise E
                            case "stop":
                                __iter.close()
                                return
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def _eval(
        self,
        __func: Callable[[_T], _R],
        /,
        *,
        exceptions: Literal["keep", "discard", "raise", "stop"] = "keep",
    ) -> Stream[_R]:
        """Eval method to catch BaseException. Not recommended."""

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for elm in _loop(__iter):
                    try:
                        yield __func(elm)
                    except BaseException as E:
                        match exceptions:
                            case "keep":
                                yield StreamException(E, elm)
                            case "discard":
                                continue
                            case "raise":
                                raise E
                            case "stop":
                                __iter.close()
                                return
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def exc(
        self,
        exc: Exception,
        todo: Literal["stop", "continue", "with", "replace"],
        /,
        __with: _R | Callable[[_T], _R] = None,
    ) -> Stream[_T | _R]:
        """The method allows to deal with Exceptions thrown by functions in the
        stream.
         - stop -> the stream is interrupted before the exception
         - continue -> the element that raises the exception gets skipped
         - replace -> the element is replaced by the item specified as __with
         - with -> the element is replaced by the result of the __with function
         with the original element (before the eval)."""
        if todo not in ("stop", "continue", "with", "replace"):
            raise ValueError

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for elm in __iter:
                    if isinstance(elm, StreamException) and isinstance(elm.exc, exc):
                        match todo:
                            case "continue":
                                continue
                            case "replace":
                                yield __with
                            case "stop":
                                __iter.close()
                                return
                            case "with":
                                try:
                                    yield __with(elm.val)
                                except Exception as E:
                                    yield StreamException(E, elm.val)
                    else:
                        yield elm
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def list(self) -> list[_T]:
        """The method consumes the stream and returns a list with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return list(_loop(self.__iter))

    def tuple(self) -> tuple[_T]:
        """The method consumes the stream and returns a tuple with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return tuple(_loop(self.__iter))

    def set(self) -> set[_T]:
        """The method consumes the stream and returns a set with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return set(_loop(self.__iter))

    def null(self) -> None:
        """The method consumes the stream, returning nothing.
        Useful to debug (Stream.print does not print until consumed)."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            try:
                for _ in _loop(__iter):
                    ...
            except GeneratorExit:
                __iter.close()
                return

        self.__iter = loop(self.__iter)
        return self

    def first(
        self, __key: Callable[[_T], bool] = lambda _: True, default: _T = None
    ) -> _T:
        """The method consumes the first item of the stream, returning it. If the
        stream is empty the default item is returned."""

        for elm in _loop(self.__iter):
            if __key(
                elm
            ):  # No try except necessary, if exception is raised it must be raised
                return elm
        return default

    def last(
        self, __key: Callable[[_T], bool] = lambda _: True, default: _T = None
    ) -> _T:
        """The method consumes the entire stream, returning only the last item.
        If the stream is empty the default item is returned."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException

        ret = default
        try:
            for elm in _loop(self.__iter):
                if __key(
                    elm
                ):  # No try except necessary, if exception is raised it must be raised
                    ret = elm
        except GeneratorExit:
            self.__iter.close()
            return ret
        return ret

    def join(self, sep: str = "", __key: Callable[[_T], bool] = lambda _: True) -> str:
        """The method consumes the stream with the join method, returning the result."""
        return sep.join(e for e in _loop(self.__iter) if __key(e))

    def sum(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        """The method consumes the stream with the sum method, returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return sum(e for e in _loop(self.__iter) if __key(e))

    def count(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        """The method consumes the stream with the len method, returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return sum(1 for e in _loop(self.__iter) if __key(e))

    def mean(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        """The method consumes the stream with the statistics.mean method,
        returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return mean(e for e in _loop(self.__iter) if __key(e))

    def all(self, __func: Callable[[_T], bool] = lambda x: x) -> bool:
        """The method consumes the stream with the all method, returning the result."""
        return all(_loop(self.__iter))

    def any(self, __func: Callable[[_T], bool] = lambda x: x) -> bool:
        """The method consumes the stream with the any method, returning the result."""
        return any(_loop(self.__iter))

    def min(self) -> _T:
        """The method consumes the stream with the min method, returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return min(_loop(self.__iter))

    def max(self) -> _T:
        """The method consumes the stream with the max method, returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return max(_loop(self.__iter))

    def split(
        self,
        __key: Callable[[_T], _H],
        /,
        *,
        exceptions: Literal["keep", "discard", "raise", "stop"] = "keep",
    ) -> dict[_H, Stream[_T]]:
        """The method returns a dict of streams. The streams are obtained by grouping,
        in order, all elements returning the same value when the __key function is
        applied to them. If an exception is raised by the __key function the key is
        obtained as such:
         ZeroDivisionError -> __exc_ZeroDivisionError"""
        if self.__length == Len.INF:
            raise UnlimitedStreamException

        out: dict[_H, list[_T]] = {}
        for elm in _loop(self.__iter):
            try:
                key = __key(elm)
            except Exception as E:
                match exceptions:
                    case "keep":
                        elm = StreamException(E, elm)
                        key = f"__exc_{E.__class__.__name__}"
                        if key not in out:
                            out[key] = list((elm,))
                        else:
                            out[key].append(elm)
                    case "discard":
                        continue
                    case "raise":
                        raise E
                    case "stop":
                        self.__iter.close()
            else:
                if key not in out:
                    out[key] = list((elm,))
                else:
                    out[key].append(elm)
        return {k: Stream(vs) for k, vs in out.items()}

    def split_list(self, __key: Callable[[_T], _H]) -> dict[_H, list[_T]]:
        """The method returns a dict of lists. The lists are obtained by grouping,
        in order, all elements returning the same value when the __key function is
        applied to them."""
        return {k: s.list() for k, s in self.split(__key).items()}

    def __iter__(self) -> Iterator[_T]:
        return _loop(self.__iter)

    # Operations to output to text

    def print(self, __format_spec: str = DEFAULT_FORMAT) -> Stream[_T]:
        """The method prints the stream by piecing together each element. The method
        does not consume by itself the stream, and it relies on other methods to
        do it, printing only when a StopIteration or GeneratorExit exception is
        raised."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException

        def loop(__iter: Generator[_T, None, None]) -> Generator[_T, None, None]:
            pre, frm, sep, end = _match_format(__format_spec)
            out = []
            try:
                for elm in _loop(__iter):
                    out.append(frm.format(elm))
                    yield elm
            except GeneratorExit:
                out.append("...")
                print(f"{pre}{sep.join(out)}{end}")
                __iter.close()
                return
            print(f"{pre}{sep.join(out)}{end}")

        self.__iter = loop(self.__iter)
        return self

    def __format__(self, __format_spec: str) -> str:
        """The method returns a string representation of the stream by consuming
        it."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        if __format_spec == "":
            __format_spec = DEFAULT_FORMAT
        pre, frm, sep, end = _match_format(__format_spec)
        return f"{pre}{sep.join(frm.format(e) for e in self)}{end}"

    def __repr__(self) -> str:
        """The method implements the default python repr function."""
        return self.__format__(DEFAULT_REPR_FORMAT)

    def __str__(self) -> str:
        """The method implements the default python str function."""
        return self.__format__(DEFAULT_FORMAT)

    # Miscellaneous

    def _length_override(self, length: Len) -> Stream[_T]:
        """The method (normally not to be used) alters the believed length of the
        generator. Some methods might raise UnlimitedStreamException if the stream
        is marked as infinite. If for whatever reason you want to deal with infinity
        or the stream is wrongfully marked you can set the length with the Len enum
        or manually setting to:
         - length = 1  : finite length
         - length = 0  : unknown length
         - length = -1 : infinite length"""
        if length not in Len.__members__.values():
            raise ValueError
        self.__length = length
        return self

    # Caching methods

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
        self.__iter = _loop_enter(_copy_method(list_cache))
        return self

    def reverse(self) -> Stream[_T]:
        """The method caches the stream and stores it onto al list, and iterates
        through it in reverse."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        list_cache = self.list()
        self.__iter = _loop_enter(reversed(list_cache))
        return self

    def shuffle(self) -> Stream[_T]:
        """The method caches the stream and stores it onto al list, and returns
        a shuffled version of the list."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        list_cache = self.list()
        self.__iter = _loop_enter(shuffle(list_cache))
        return self
