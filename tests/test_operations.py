from streams import Stream


def test_zip() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 10)
    stream_zip = Stream.zip(stream_a, stream_b)
    assert str(stream_zip) == "<(0, 5), (1, 6), (2, 7), (3, 8), (4, 9)>"


def test_zip_longest() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 11)
    stream_zip_longest = Stream.zip_longest(stream_a, stream_b)
    assert (
        str(stream_zip_longest)
        == "<(0, 5), (1, 6), (2, 7), (3, 8), (4, 9), (None, 10)>"
    )


# def test_round_robin() -> None:
#     stream_a = Stream.range(5)
#     stream_b = Stream.range(5, 10)
#     stream_round_robin = Stream.round_robin(stream_a, stream_b)
#     assert stream_round_robin == 


def test_operate() -> None:
    stream_a = Stream.range(5)
    stream_b = Stream.range(5, 10)
    stream_operate = Stream.operate(lambda x, y: x + y, stream_a, stream_b)
    assert str(stream_operate) == "<5, 7, 9, 11, 13>"
