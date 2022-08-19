from streams import Stream
import pytest


def test_zip() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 10)
    stream_zip = Stream.zip(stream_a, stream_b)
    assert str(stream_zip) == "<(0, 5), (1, 6), (2, 7), (3, 8), (4, 9)>"


def test_zip_strict() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 9)
    stream_zip = Stream.zip(stream_a, stream_b, strict=True)
    pytest.raises(ValueError, stream_zip.list)


def test_zip_longest() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 11)
    stream_zip_longest = Stream.zip_longest(stream_a, stream_b)
    STREAM_RESULT = "<(0, 5), (1, 6), (2, 7), (3, 8), (4, 9), (None, 10)>"
    assert str(stream_zip_longest) == STREAM_RESULT


def test_round_robin() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 10)
    stream_round_robin = Stream.round_robin(stream_a, stream_b)
    assert str(stream_round_robin) == "<0, 5, 1, 6, 2, 7, 3, 8, 4, 9>"


def test_round_robin_strict() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 9)
    stream_round_robin = Stream.round_robin(stream_a, stream_b, strict=True)
    pytest.raises(ValueError, stream_round_robin.list)


def test_round_robin_longest_fill() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 11)
    stream_round_robin = Stream.round_robin_longest(stream_a, stream_b, fillvalue=None)
    assert str(stream_round_robin) == "<0, 5, 1, 6, 2, 7, 3, 8, 4, 9, None, 10>"


def test_round_robin_longest() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 11)
    stream_round_robin = Stream.round_robin_longest(stream_a, stream_b)
    assert str(stream_round_robin) == "<0, 5, 1, 6, 2, 7, 3, 8, 4, 9, 10>"


def test_operate() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 10)
    stream_operate = Stream.operate(lambda x, y: x + y, stream_a, stream_b)
    assert str(stream_operate) == "<5, 7, 9, 11, 13>"

def test_operate() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 10)
    stream_operate = Stream.operate_iter(sum, stream_a, stream_b)
    assert str(stream_operate) == "<5, 7, 9, 11, 13>"

def test_zip_exceptions() -> None:
    stream_a = (
        Stream.range(3).eval(lambda x: 1 / x).exc(ZeroDivisionError, "replace", -1)
    )
    stream_b = (
        Stream.range(3).eval(lambda x: 1 / x).exc(ZeroDivisionError, "replace", -1)
    )
    stream_zip = Stream.zip(stream_a, stream_b)
    assert str(stream_zip) == "<(-1, -1), (1.0, 1.0), (0.5, 0.5)>"
