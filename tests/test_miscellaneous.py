from streams import Stream, min_length, max_length, Len
import pytest


def test_min_length() -> None:
    stream_INF = Stream.empty()._length_override(Len.INF)
    stream_UNK = Stream.empty()._length_override(Len.UNK)
    stream_FIN = Stream.empty()._length_override(Len.FIN)

    assert min_length(stream_INF, stream_UNK) == Len.UNK
    assert min_length(stream_INF, stream_FIN) == Len.FIN
    assert min_length(stream_UNK, stream_FIN) == Len.FIN
    assert min_length(stream_INF, stream_INF) == Len.INF
    assert min_length(stream_UNK, stream_UNK) == Len.UNK
    assert min_length(stream_FIN, stream_FIN) == Len.FIN


def test_max_length() -> None:
    stream_INF = Stream.empty()._length_override(Len.INF)
    stream_UNK = Stream.empty()._length_override(Len.UNK)
    stream_FIN = Stream.empty()._length_override(Len.FIN)

    assert max_length(stream_INF, stream_UNK) == Len.INF
    assert max_length(stream_INF, stream_FIN) == Len.INF
    assert max_length(stream_UNK, stream_FIN) == Len.UNK
    assert max_length(stream_INF, stream_INF) == Len.INF
    assert max_length(stream_UNK, stream_UNK) == Len.UNK
    assert max_length(stream_FIN, stream_FIN) == Len.FIN

def test_length_override() -> None:
    stream = Stream.empty()
    pytest.raises(ValueError, stream._length_override, 1)


def test_cache() -> None:
    list_cache = []
    stream_cache = Stream.range(0, 10).cache(list_cache)
    assert list_cache == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert str(stream_cache) == "<0, 1, 2, 3, 4, 5, 6, 7, 8, 9>"


def test_reverse() -> None:
    stream_reverse = Stream.range(0, 10).reverse()
    assert str(stream_reverse) == "<9, 8, 7, 6, 5, 4, 3, 2, 1, 0>"
