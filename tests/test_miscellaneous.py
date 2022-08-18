from streams import Stream, min_length, max_length, Len


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
