from __future__ import annotations
from enum import Enum
from itertools import count, zip_longest
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


def _next(__i: Iterable[_T]) -> _T:
    """Wrapper for python next(__i) with check for StreamExceptions."""
    nx = next(__i)
    if isinstance(nx, StreamException):
        raise nx.exc
    return nx


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
        possible it is recommended to prefer using the default generators,
        such as range and count.

        >>> Stream([1,2,3,4,5]) -> <1,2,3,4,5>
        >>> Stream.range(4)    -> <0,1,2,3>
        >>> Stream.primes().limit(3) -> <2,3,5>"""
        self.__iter = __iter
        if length == None:
            try:
                len(self.__iter)
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
        cls, __start: SupportsIndex, __stop: SupportsIndex, __step: SupportsIndex, /
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
    def empty(cls) -> Stream:
        """The method generates an empty stream."""
        return cls([], Len.FIN)

    # Class methods to operate with streams

    @classmethod
    def zip(cls, *streams: Stream[_T], strict: bool = False) -> Stream[_T]:
        """The method joins multiple streams with the zip python method, returning
        a new stream of tuples. The stream ends when the first stream ends.
        If strict is set then ValueError is raised if one stream ends before the others."""
        return cls(zip(*streams, strict=strict), min_length(*streams))

    @classmethod
    def zip_longest(cls, *streams: Stream[_T], fillvalue: Any = None) -> Stream[_T]:
        """The method joins multiple streams with the zip_longest python method,
        returning a new stream of tuples. The stream ends when the last stream ends.
        Streams that end first are continued with fillvalue."""
        return cls(zip_longest(*streams, fillvalue=fillvalue), max_length(*streams))

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

    @classmethod
    def round_robin_longest(
        cls, *streams: Stream[_T], fillvalue: Any = NoFillValue
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

    def filter(self, __key: Callable[[_T], bool], keep_if: bool = True) -> Stream[_T]:
        """The method iterates through the stream evaluating each element via the
        __key function. All values which do not return the same value as keep_if
        are discarded."""

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
        """The method allows to select a slice of the stream via the start, stop,
        step parameters."""
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
        """The method allows to skip a number of items, resuming the stream after
        the specified amount."""

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
        """The method cuts the stream after the specified amount of item is yielded."""
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
        """The method stops the stream when the __when function evaluates to true.
        If set to true, the inclusive parameter prints the element that evaluated
        to true before interrupting the stream."""
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
        """The method removes all elements that repeat in the stream. It is to be
        noted that it uses a set to cache the elements, therefore the elements must
        be hashable."""
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
        """The mehtod functions in the same way that the enumerate object functions
        in normal python, by yielding tuples in the form of (index, value)."""

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
        """The method replaces every instance of __old with __new."""

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
        """The method replaces every element with the output of the __with function.
        If set, the __when function determines whether or not to change the element.
        Exceptions thrown by either __with or __when are caught as StreamException,
        and can be dealt with in a subsequent .exc method. Any exception that is not
        caught in this way is raised in any subsequent method."""

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
        """The method replaces every element of the stream with the output of the
        __func function.
        Exceptions thrown by __func are caught as StreamException, and can be dealt
        with in a subsequent .exc method. Any exception that is not caught in this
        way is raised in any subsequent method.
        In order to catch BaseExceptions you can call the _eval method, but it is
        not recommended to use it except in specific circumstances."""

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

    def _eval(self, __func: Callable[[_T], _R]) -> Stream[_R]:
        """Eval method to catch BaseException. Not recommended."""

        def loop(__iter: Iterable[_T]) -> Iterable[_T]:
            try:
                it = iter(__iter)
                while True:
                    nx = _next(it)
                    try:
                        yield __func(nx)
                    except BaseException as E:
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
        """The method allows to deal with Exceptions thrown by functions in the
        stream.
         - stop -> the stream is interrupted before the exception
         - continue -> the element that raises the exception gets skipped
         - replace -> the element is replaced by the item specified as __with
         - with -> the element is replaced by the result of the __with function
         with the original element (before the eval)."""
        if todo not in ("stop", "continue", "with", "replace"):
            raise ValueError

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
        """The method consumes the stream and returns a list with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return list(self._loop())

    def tuple(self) -> tuple[_T]:
        """The method consumes the stream and returns a tuple with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return tuple(self._loop())

    def set(self) -> set[_T]:
        """The method consumes the stream and returns a set with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return set(self._loop())

    def null(self) -> None:
        """The method consumes the stream, returning nothing.
        Useful to debug (Stream.print does not print until consumed)."""
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
        """The method consumes the first item of the stream, returning it. If the
        stream is empty the default item is returned."""
        try:
            it = iter(self._loop_key(__key))
            return next(it)
        except StopIteration:
            return default

    def last(
        self, __key: Callable[[_T], bool] = lambda _: True, default: _T = None
    ) -> _T:
        """The method consumes the entire stream, returning only the last item.
        If the stream is empty the default item is returned."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        try:
            it = iter(self._loop_key(__key))
            nx = default
            while True:
                nx = next(it)
        except StopIteration:
            return nx

    def join(self, sep: str = "", __key: Callable[[_T], bool] = lambda _: True) -> str:
        """The method consumes the stream with the join method, returning the result."""
        return sep.join(e for e in self._loop() if __key(e))

    def sum(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        """The method consumes the stream with the sum method, returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return sum(e for e in self._loop() if __key(e))

    def count(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        """The method consumes the stream with the len method, returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return sum(1 for e in self._loop() if __key(e))

    def mean(self, __key: Callable[[_T], bool] = lambda _: True) -> _T:
        """The method consumes the stream with the statistics.mean method,
        returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return mean(e for e in self._loop() if __key(e))

    def all(self, __func: Callable[[_T], bool] = lambda x: x) -> bool:
        """The method consumes the stream with the all method, returning the result."""
        return all(self._loop())

    def any(self, __func: Callable[[_T], bool] = lambda x: x) -> bool:
        """The method consumes the stream with the any method, returning the result."""
        return any(self._loop())

    def min(self) -> _T:
        """The method consumes the stream with the min method, returning the result."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return min(self._loop())

    def max(self) -> _T:
        """The method consumes the stream with the max method, returning the result."""
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
        """The method prints the stream by piecing together each element. The method
        does not consume by itself the stream, and it relies on other methods to
        do it, printing only when a StopIteration or GeneratorExit exception is
        raised."""
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
