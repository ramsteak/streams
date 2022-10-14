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
    Union,
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

_NotSet = object()

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

    def __init__(self, __iter: Generator[_T, None, None], length: Len = None) -> None:
        """The method generates a stream object from any iterable, consuming it
        lazily when needed. The length parameter is to be set when the length
        cannot be determined automatically (such as iterables without a __len__
        method or methods where calling __len__ would consume them). Whenever
        possible it is preferrable to use the default generators, such as range
        and count.

        >>> Stream([1, 2, 3, 4, 5]) -> <1, 2, 3, 4, 5>
        >>> Stream.range(4)    -> <0, 1, 2, 3>
        >>> Stream.primes().limit(3) -> <2, 3, 5>"""

        self.__cache = list[_T]()
        self.__iter = iter(__iter)
        # -         self.__iter = _loop(__iter)

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

    # region Class methods for special streams

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

    # endregion
    # region Class methods to operate with streams

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
    ) -> Stream[tuple[Union[_T, _R]]]:
        ...

    @overload
    @classmethod
    def zip_longest(
        cls, stream: Stream[_T], stream1: Stream[_T1], fillvalue: _R = None
    ) -> Stream[tuple[Union[_T, _R], Union[_T1, _R]]]:
        ...

    @overload
    @classmethod
    def zip_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        fillvalue: _R = None,
    ) -> Stream[tuple[Union[_T, _R], Union[_T1, _R], Union[_T2, _R]]]:
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
    ) -> Stream[tuple[Union[_T, _R], Union[_T1, _R], Union[_T2, _R], Union[_T3, _R]]]:
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
    ) -> Stream[
        tuple[
            Union[_T, _R],
            Union[_T1, _R],
            Union[_T2, _R],
            Union[_T3, _R],
            Union[_T4, _R],
        ]
    ]:
        ...

    @overload
    @classmethod
    def zip_longest(
        cls, *streams: Stream[_T], fillvalue: _R = None
    ) -> Stream[Union[_T, _R]]:
        ...

    @classmethod
    def zip_longest(
        cls, *streams: Stream[_T], fillvalue: _R = None
    ) -> Stream[Union[_T, _R]]:
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
    ) -> Stream[Union[_T, _T1]]:
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
    ) -> Stream[Union[_T, _T1, _T2]]:
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
    ) -> Stream[Union[_T, _T1, _T2, _T3]]:
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
    ) -> Stream[Union[_T, _T1, _T2, _T3, _T4]]:
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
    ) -> Stream[Union[_T, _R]]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls, stream: Stream[_T], stream1: Stream[_T1], *, fillvalue: _R
    ) -> Stream[Union[_T, _T1, _R]]:
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
    ) -> Stream[Union[_T, _T1, _T2, _R]]:
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
    ) -> Stream[Union[_T, _T1, _T2, _T3, _R]]:
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
    ) -> Stream[Union[_T, _T1, _T2, _T3, _T4, _R]]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls, *streams: Stream[_T], fillvalue: _R
    ) -> Stream[Union[_T, _R]]:
        ...

    @overload
    @classmethod
    def round_robin_longest(cls, stream: Stream[_T]) -> Stream[_T]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls, stream: Stream[_T], stream1: Stream[_T1]
    ) -> Stream[Union[_T, _T1]]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls, stream: Stream[_T], stream1: Stream[_T1], stream2: Stream[_T2]
    ) -> Stream[Union[_T, _T1, _T2]]:
        ...

    @overload
    @classmethod
    def round_robin_longest(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
    ) -> Stream[Union[_T, _T1, _T2, _T3]]:
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
    ) -> Stream[Union[_T, _T1, _T2, _T3, _T4]]:
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
    def chain(cls, stream: Stream[_T], stream1: Stream[_T1]) -> Stream[Union[_T, _T1]]:
        ...

    @overload
    @classmethod
    def chain(
        cls, stream: Stream[_T], stream1: Stream[_T1], stream2: Stream[_T2]
    ) -> Stream[Union[_T, _T1, _T2]]:
        ...

    @overload
    @classmethod
    def chain(
        cls,
        stream: Stream[_T],
        stream1: Stream[_T1],
        stream2: Stream[_T2],
        stream3: Stream[_T3],
    ) -> Stream[Union[_T, _T1, _T2, _T3]]:
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
    ) -> Stream[Union[_T, _T1, _T2, _T3, _T4]]:
        ...

    @overload
    @classmethod
    def chain(cls, *streams: Stream[_T]) -> Stream[_T]:
        ...

    @classmethod
    def chain(cls, *streams: Stream[_T]) -> Stream[_T]:
        """The method concatenates multiple streams into one single stream. Only the
        last stream may be infinite."""
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

    # endregion
    # region Operations to limit the data items

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

        def loop(__iter: Stream[_T]) -> Generator[_T, None, None]:
            try:
                for elm in __iter:
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
            except StopIteration:
                return

        return Stream(loop(self))

    def slice(self, start: int, stop: int, step: int = 1) -> Stream[_T]:
        """The method allows to select a slice of the stream via the start, stop,
        step parameters."""
        ret = (
            self.enumerate().filter(lambda i: i[0] in range(start, stop, step)).denum()
        )
        ret.__length = Len.FIN
        if step < 1:
            raise ValueError("Step value must be 1 or greater")
        if start > stop:
            raise ValueError("Start value must be smaller than stop value")

        return ret

    def skip(self, count: int) -> Stream[_T]:
        """The method allows to skip a number of items, resuming the stream after
        the specified amount."""

        return self.enumerate().filter(lambda i: i[0] >= count).denum()

    def limit(self, count: int) -> Stream[_T]:
        """The method cuts the stream after the specified amount of item is yielded."""
        # self.__length = Len.FIN

        ret = self.enumerate().stop(lambda x: x[0] >= count - 1, inclusive=True).denum()
        ret.__length = Len.FIN
        return ret

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

        def loop(__iter: Stream[_T]) -> Generator[_T, None, None]:
            try:
                for elm in __iter:
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
            except StopIteration:
                return

        ret = Stream(loop(self))
        if ret.length == Len.INF:
            ret.__length = Len.UNK

        return ret

    def distinct(self) -> Stream[_T]:
        class remember:
            def __init__(self) -> None:
                self.__mem = set()

            def __call__(self, __item: _T) -> bool:
                if __item not in self.__mem:
                    self.__mem.add(__item)
                    return True
                return False

        mem = remember()
        return self.filter(mem)

    # endregion
    # region Operations to change the data items

    def enumerate(self) -> Stream[tuple[int, _T]]:
        """The mehtod functions in the same way that the enumerate object functions
        in normal python, by yielding tuples in the form of (index, value)."""

        def loop(__iter: Stream[_T]) -> Generator[_T, None, None]:
            try:
                for i, elm in enumerate(__iter):
                    yield (i, elm)
            except GeneratorExit:
                __iter.close()
                return
            except StopIteration:
                return

        return Stream(loop(self))

    def denum(self) -> Stream[_T]:
        """The method is a shorthand way to remove the enumeration.
        It is a quick replacement for .eval(lambda x:x[1])."""
        return self.eval(lambda x: x[1])

    def replace(self, __old: _T, __new: _R) -> Stream[Union[_T, _R]]:
        """The method replaces every instance of __old with __new."""

        return self.eval(lambda x: __new if x == __old else x)

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

        def loop(__iter: Stream[_T]) -> Generator[_T, None, None]:
            try:
                for elm in __iter:
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
            except StopIteration:
                return

        return Stream(loop(self))

    def eval_u(
        self,
        __func: Callable[[_T], _R],
        /,
        *,
        exceptions: Literal["keep", "discard", "raise", "stop"] = "keep",
    ) -> Stream[_R]:
        """The method replaces every element of the stream with the output of the
        __func function, unpacking the item to use as arguments to the function.
        Exceptions thrown by __func are caught as StreamException, and can be dealt
        with in a subsequent .exc method. Any exception that is not caught in this
        way is raised in any subsequent method."""
        return self.eval(lambda x: __func(*x), exceptions=exceptions)

    def exc(
        self,
        exc: Exception,
        todo: Literal["stop", "discard", "with", "replace"] = "discard",
        /,
        __with: Union[_R, Callable[[_T], _R]] = None,
    ) -> Stream[Union[_T, _R]]:
        """The method allows to deal with Exceptions thrown by functions in the
        stream.
         - stop -> the stream is interrupted before the exception
         - discard -> the element that raises the exception gets skipped
         - replace -> the element is replaced by the item specified as __with
         - with -> the element is replaced by the result of the __with function
         with the original element (before the eval)."""
        if todo not in ("stop", "discard", "with", "replace"):
            raise ValueError
        
        def loop(__iter: Stream[_T]) -> Generator[_T, None, None]:
            try:
                while True:
                    elm = __iter.__next_sxc__()
                    if isinstance(elm, StreamException):
                        match todo:
                            case "discard":
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
            except StopIteration:
                return
        
        return Stream(loop(self))

    def list(self) -> list[_T]:
        """The method consumes the stream and returns a list with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return list(self)

    def tuple(self) -> tuple[_T]:
        """The method consumes the stream and returns a tuple with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return tuple(self)

    def set(self) -> set[_T]:
        """The method consumes the stream and returns a set with the items of the
        stream."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        return set(self)

    def null(self) -> None:
        """The method consumes the stream, returning nothing.
        Useful to debug (Stream.print does not print until consumed)."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        for _ in self:
            ...
        return self

    def first(self, default: _T = _NotSet, consume: bool = True) -> _T:
        """The method consumes the first item of the stream, returning it. If the
        stream is empty the default item is returned."""
        try:
            f = next(self)
        except StopIteration:
            if default is _NotSet:
                raise StopIteration
            return default
        if not consume:
            self.__cache.insert(0, f)
        return f

    def last(self, default: _T = _NotSet, consume: bool = True) -> _T:
        self.cache()
        if self.__cache:
            if not consume:
                return self.__cache[-1]
            else:
                return self.__cache.pop()
        else:
            if default is _NotSet:
                raise StopIteration
            else:
                return default

    def _loopovr(
        self,
        __key: Callable[[_T], bool],
        consume: bool,
        method: Callable[[Iterable[_T]], _T],
    ) -> _T:
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        if not consume:
            self.cache()
            return method(e for e in self.__cache if __key(e))
        else:
            return method(e for e in self if __key(e))

    def sum(
        self, __key: Callable[[_T], bool] = lambda _: True, consume: bool = True
    ) -> _T:
        return self._loopovr(__key, consume, sum)

    def count(
        self, __key: Callable[[_T], bool] = lambda _: True, consume: bool = True
    ) -> _T:
        def cnt(__it:Iterable[Any]) -> int: return sum(1 for _ in __it)
        return self._loopovr(__key, consume, cnt)

    def mean(
        self, __key: Callable[[_T], bool] = lambda _: True, consume: bool = True
    ) -> _T:
        return self._loopovr(__key, consume, mean)

    def all(
        self, __key: Callable[[_T], bool] = lambda _: True, consume: bool = True
    ) -> _T:
        return self._loopovr(__key, consume, all)

    def any(
        self, __key: Callable[[_T], bool] = lambda _: True, consume: bool = True
    ) -> _T:
        return self._loopovr(__key, consume, any)

    def min(
        self, __key: Callable[[_T], bool] = lambda _: True, consume: bool = True
    ) -> _T:
        return self._loopovr(__key, consume, min)

    def max(
        self, __key: Callable[[_T], bool] = lambda _: True, consume: bool = True
    ) -> _T:
        return self._loopovr(__key, consume, max)
    
    def report(self) -> dict[str, _T]:
        """The method consumes the stream and returns a dict with multiple informations
        about the stream, such as length, sum, min, max, mean"""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        it = enumerate(self)
        ret = {"count": 0}
        try:
            while True:
                index, val = next(it)
                try:
                    if ret["min"] > val:
                        ret["min"] = val
                    if ret["max"] < val:
                        ret["max"] = val
                    ret["sum"] += val
                except KeyError:
                    ret["min"], ret["max"], ret["sum"] = val, val, val
        except StopIteration:
            ret["count"] = index + 1
            ret["mean"] = ret["sum"] / ret["count"]
        return ret

    def split(self, __key: Callable[[_T], _H],/,*, exceptions:Literal["keep","discard","raise","stop"]="keep") -> dict[_H, Stream[_T]]:
        ...

#     def split(
#         self,
#         __key: Callable[[_T], _H],
#         /,
#         *,
#         exceptions: Literal["keep", "discard", "raise", "stop"] = "keep",
#     ) -> dict[_H, Stream[_T]]:
#         """The method returns a dict of streams. The streams are obtained by grouping,
#         in order, all elements returning the same value when the __key function is
#         applied to them. If an exception is raised by the __key function the key is
#         obtained as such:
#          ZeroDivisionError -> __exc_ZeroDivisionError"""
#         if self.__length == Len.INF:
#             raise UnlimitedStreamException

#         out: dict[_H, list[_T]] = {}
#         for elm in _loop(self.__iter):
#             try:
#                 key = __key(elm)
#             except Exception as E:
#                 match exceptions:
#                     case "keep":
#                         elm = StreamException(E, elm)
#                         key = f"__exc_{E.__class__.__name__}"
#                         if key not in out:
#                             out[key] = list((elm,))
#                         else:
#                             out[key].append(elm)
#                     case "discard":
#                         continue
#                     case "raise":
#                         raise E
#                     case "stop":
#                         self.__iter.close()
#             else:
#                 if key not in out:
#                     out[key] = list((elm,))
#                 else:
#                     out[key].append(elm)
#         return {k: Stream(vs) for k, vs in out.items()}

#     def split_list(self, __key: Callable[[_T], _H]) -> dict[_H, list[_T]]:
#         """The method returns a dict of lists. The lists are obtained by grouping,
#         in order, all elements returning the same value when the __key function is
#         applied to them."""
#         return {k: s.list() for k, s in self.split(__key).items()}

    def __iter__(self) -> Iterator[_T]:
        return self

    def __next__(self) -> _T:
        if self.__cache:
            nx = self.__cache.pop(0)
        else:
            nx = self.__iter.__next__()
        if isinstance(nx, StreamException):
            raise nx.exc
        return nx

    def __next_sxc__(self) -> _T:
        if self.__cache:
            return self.__cache.pop(0)
        else:
            try:
                return self.__iter.__next_sxc__()
            except AttributeError:
                return self.__iter.__next__()
    
    def __next_noch__(self) -> _T:
        try:
            return self.__iter.__next_noch__()
        except AttributeError:
            return self.__iter.__next__()
    # endregion
    # region Operations to output to text

    def print(self, __format_spec: str = DEFAULT_FORMAT) -> Stream[_T]:
        """The method prints the stream by piecing together each element. The method
        does not consume by itself the stream, and it relies on other methods to
        do it, printing only when a StopIteration or GeneratorExit exception is
        raised."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException

        def loop(__iter: Stream[_T]) -> Generator[_T, None, None]:
            pre, frm, sep, end = _match_format(__format_spec)
            out = []
            try:
                for elm in __iter:
                    out.append(frm.format(elm))
                    yield elm
            except GeneratorExit:
                out.append("...")
                print(f"p:{pre}{sep.join(out)}{end}")
                __iter.close()
                return
            print(f"p:{pre}{sep.join(out)}{end}")

        return Stream(loop(self))

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
        # return str(self.__cache) + '...'
        return self.__format__(DEFAULT_REPR_FORMAT)

    def __str__(self) -> str:
        """The method implements the default python str function."""
        # return str(self.__cache) + '...'
        return self.__format__(DEFAULT_FORMAT)

    # endregion
    # region Miscellaneous

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

    # endregion
    def reverse(self) -> Stream[_T]:
        """The method caches the stream and stores it onto al list, and iterates
        through it in reverse."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        self.cache()
        return Stream(reversed(self.__cache))

    def shuffle(self) -> Stream[_T]:
        """The method caches the stream and stores it onto al list, and returns
        a shuffled version of the list."""
        if self.__length == Len.INF:
            raise UnlimitedStreamException
        self.cache()
        return Stream(shuffle(self.__cache))  # TODO: non mi piace molto

    def cache(self, n: int = None) -> Stream[_T]:
        """The method stores the values of the stream in its cache to potentially
        speed up processing (e.g. evaluating during free time).
        If n is not set then it caches the whole stream"""
        if n is None:
            if self.__length == Len.INF:
                raise UnlimitedStreamException
            try:
                while True:
                    self.__cache.append(self.__next_noch__())
            except StopIteration:
                ...
        else:
            for _ in range(n):
                try:
                    self.__cache.append(self.__iter.__next__())
                except StopIteration:
                    break
        return self

    def close(self) -> None:
        self.__cache.clear()
        try:
            self.__iter.close()
        except AttributeError:
            return
