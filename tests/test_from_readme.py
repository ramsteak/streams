from streams import Stream
import pytest

def test_1() -> None:
    stream = (Stream.range(10)
                .filter(lambda x:x%2))

    stream_list = stream.list()
    assert stream_list == [1, 3, 5, 7, 9]

def test_2() -> None:
    stream = (Stream
                .range(3)
                .eval(lambda x:1/x)
                .exc(ZeroDivisionError, 'replace', float('inf')))

    stream_list = stream.list()
    assert stream_list == [float('inf'), 1.0, 0.5]

def test_3() -> None:
    stream = (Stream.range(3)
                .eval(lambda x:1/x))
    pytest.raises(ZeroDivisionError, stream.list)