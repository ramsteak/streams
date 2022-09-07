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


def test_exc_discard() -> None:
    stream = (
        Stream.range(0, 2, 1).eval(lambda x: 1 / x).exc(ZeroDivisionError, "discard")
    )
    assert str(stream) == "<1.0>"


def test_eval_exception_uncaught() -> None:
    stream = Stream.range(3).eval(lambda x: 1 / x)
    pytest.raises(ZeroDivisionError, stream.list)


def test_replace_exception_uncaught() -> None:
    stream = Stream.range(3).replace_with(lambda x: 1 / x, lambda _: True)
    pytest.raises(ZeroDivisionError, stream.list)


def test_eval_exception_in_exc() -> None:
    stream = Stream.range(3).eval(lambda x: 1 / x).exc(ZeroDivisionError, "replace", 1)
    assert str(stream) == "<1, 1.0, 0.5>"


def test_replace_exception_in_exc() -> None:
    stream = (
        Stream.range(3)
        .replace_with(lambda x: 1 / x)
        .exc(ZeroDivisionError, "replace", 1)
    )
    assert str(stream) == "<1, 1.0, 0.5>"


def test_eval_exception_in_exc_uncaught() -> None:
    stream = (
        Stream.range(3)
        .eval(lambda x: 1 / x)
        .exc(ZeroDivisionError, "with", lambda x: 1 / x)
    )
    pytest.raises(ZeroDivisionError, stream.list)


def test_stop_stop_exception() -> None:
    stream = Stream.range(3).stop(lambda x: 1 / x < 0.33, exceptions="stop")
    assert str(stream) == "<>"


def test_stop_keep_exception() -> None:
    stream = Stream.range(3).stop(lambda x: 1 / x < 0.33, exceptions="keep")
    assert str(stream) == "<0, 1, 2>"


def test_stop_raise_exception() -> None:
    stream = Stream.range(3).stop(lambda x: 1 / x < 0.33, exceptions="raise")
    pytest.raises(ZeroDivisionError, stream.list)


def test_stop_discard_exception() -> None:
    stream = Stream.range(3).stop(lambda x: 1 / x < 0.33, exceptions="discard")
    assert str(stream) == "<1, 2>"


def test_filter_stop_exception() -> None:
    stream = Stream.range(3).filter(lambda x: 1 / x >= 1, exceptions="stop")
    assert str(stream) == "<>"


def test_filter_keep_exception() -> None:
    stream = Stream.range(3).filter(lambda x: 1 / x >= 1, exceptions="keep")
    assert str(stream) == "<0, 1>"


def test_filter_raise_exception() -> None:
    stream = Stream.range(3).filter(lambda x: 1 / x >= 1, exceptions="raise")
    pytest.raises(ZeroDivisionError, stream.list)


def test_filter_discard_exception() -> None:
    stream = Stream.range(3).filter(lambda x: 1 / x >= 1, exceptions="discard")
    assert str(stream) == "<1>"


def test_replacewith_stop_exception() -> None:
    stream = Stream.range(3).replace_with(
        lambda x: 1 / x, lambda _: True, exceptions="stop"
    )
    assert str(stream) == "<>"


def test_replacewith_keep_exception() -> None:
    stream = Stream.range(3).replace_with(
        lambda x: 1 / x, lambda _: True, exceptions="keep"
    )
    pytest.raises(ZeroDivisionError, stream.list)
    stream = (
        Stream.range(3)
        .replace_with(lambda x: 1 / x, lambda _: True, exceptions="keep")
        .exc(ZeroDivisionError, "discard")
    )
    assert str(stream) == "<1.0, 0.5>"


def test_replacewith_raise_exception() -> None:
    stream = Stream.range(3).replace_with(
        lambda x: 1 / x, lambda _: True, exceptions="raise"
    )
    pytest.raises(ZeroDivisionError, stream.list)


def test_replacewith_discard_exception() -> None:
    stream = Stream.range(3).replace_with(
        lambda x: 1 / x, lambda _: True, exceptions="discard"
    )
    assert str(stream) == "<1.0, 0.5>"


def test_split_stop_exception() -> None:
    stream = Stream.range(3).split(lambda x: 1 / x > 0.7, exceptions="stop")
    assert str(stream) == "{}"


# def test_split_keep_exception() -> None:
#     def do(): return Stream.range(3).split(lambda x:1/x > 0.7, exceptions='keep')
#     pytest.raises(ZeroDivisionError, do)
def test_split_raise_exception() -> None:
    def do():
        return Stream.range(3).split(lambda x: 1 / x > 0.7, exceptions="raise")

    pytest.raises(ZeroDivisionError, do)


def test_split_discard_exception() -> None:
    stream = Stream.range(3).split(lambda x: 1 / x > 0.7, exceptions="discard")
    assert str(stream) == "{True: <1>, False: <2>}"
