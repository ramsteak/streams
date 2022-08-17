from streams import Stream
import pytest


def test_eval() -> None:
    stream = Stream.range(5).eval(lambda x: x + 2)
    assert str(stream) == "<2, 3, 4, 5, 6>"


def test_exc_replace_ZeroDivisionError() -> None:
    stream = (
        Stream.range(0, 2, 1)
        .eval(lambda x: 1 / x)
        .exc(ZeroDivisionError, "replace", -1)
    )
    assert str(stream) == "<-1, 1.0>"


def test_exc_with_ZeroDivisionError() -> None:
    stream = (
        Stream.range(0, 2, 1)
        .eval(lambda x: 1 / x)
        .exc(ZeroDivisionError, "with", lambda x: x)
    )
    assert str(stream) == "<0, 1.0>"


def test_exc_stop_ZeroDivisionError() -> None:
    stream = Stream.range(0, 2, 1).eval(lambda x: 1 / x).exc(ZeroDivisionError, "stop")
    assert str(stream) == "<>"


def test_exc_continue_ZeroDivisionError() -> None:
    stream = (
        Stream.range(0, 2, 1).eval(lambda x: 1 / x).exc(ZeroDivisionError, "continue")
    )
    assert str(stream) == "<1.0>"


def test_eval_exceptionUncaught() -> None:
    stream = Stream.range(0, 2, 1).eval(lambda x: 1 / x)
    pytest.raises(ZeroDivisionError, stream.list)
