from streams import Stream
import pytest


def test_eval() -> None:
    stream = Stream.range(5).eval(lambda x: x + 2)
    assert str(stream) == "<2, 3, 4, 5, 6>"


def test_replace_with() -> None:
    stream = Stream.range(5).replace_with(str, lambda x: x % 2)
    assert repr(stream) == "<0, '1', 2, '3', 4>"


def test_exc_replace() -> None:
    stream = (
        Stream.range(0, 2, 1)
        .eval(lambda x: 1 / x)
        .exc(ZeroDivisionError, "replace", -1)
    )
    assert str(stream) == "<-1, 1.0>"


def test_exc_with() -> None:
    stream = (
        Stream.range(0, 2, 1)
        .eval(lambda x: 1 / x)
        .exc(ZeroDivisionError, "with", lambda x: x)
    )
    assert str(stream) == "<0, 1.0>"


def test_exc_stop() -> None:
    stream = Stream.range(0, 2, 1).eval(lambda x: 1 / x).exc(ZeroDivisionError, "stop")
    assert str(stream) == "<>"


def test_exc_continue() -> None:
    stream = (
        Stream.range(0, 2, 1).eval(lambda x: 1 / x).exc(ZeroDivisionError, "continue")
    )
    assert str(stream) == "<1.0>"


def test_eval_exception_uncaught() -> None:
    stream = Stream.range(2).eval(lambda x: 1 / x)
    pytest.raises(ZeroDivisionError, stream.list)


def test_replace_exception_uncaught() -> None:
    stream = Stream.range(2).replace_with(lambda x:1/x, lambda _:True)
    pytest.raises(ZeroDivisionError, stream.list)


def test_eval_exception_in_exc() -> None:
    stream = (
        Stream.range(2).eval(lambda x: 1 / x).exc(ZeroDivisionError, "replace", 1)
    )
    assert str(stream) == "<1, 1.0>"

def test_replace_exception_in_exc() -> None:
    stream = (
        Stream.range(2).replace_with(lambda x: 1 / x).exc(ZeroDivisionError, "replace", 1)
    )
    assert str(stream) == "<1, 1.0>"


def test_eval_exception_in_exc_uncaught() -> None:
    stream = (
        Stream.range(2)
        .eval(lambda x: 1 / x)
        .exc(ZeroDivisionError, "with", lambda x: 1 / x)
    )
    pytest.raises(ZeroDivisionError, stream.list)
