from streams import Stream


def test_list() -> None:
    stream_list = Stream.range(0, 10).list()
    assert stream_list == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_tuple() -> None:
    stream_tuple = Stream.range(0, 10).tuple()
    assert stream_tuple == (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)


def test_set() -> None:
    stream_set = Stream.range(0, 10).set()
    assert stream_set == {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}


def test_first() -> None:
    stream_first = Stream.range(0, 10).first()
    assert stream_first == 0


def test_last() -> None:
    stream_last = Stream.range(0, 10).last()
    assert stream_last == 9


def test_join() -> None:
    stream_join = Stream.repeat("s").limit(20).join("")
    assert stream_join == "ssssssssssssssssssss"


def test_sum() -> None:
    stream_sum = Stream.range(0, 10).sum()
    assert stream_sum == 45


def test_count() -> None:
    stream_count = Stream.range(0, 10).count()
    assert stream_count == 10


def test_mean() -> None:
    stream_mean = Stream.range(0, 10).mean()
    assert stream_mean == 4.5


def test_all() -> None:
    stream_all = Stream.range(0, 10).all()
    assert stream_all is False


def test_any() -> None:
    stream_any = Stream.range(0, 10).any()
    assert stream_any is True


def test_min() -> None:
    stream_min = Stream.range(0, 10).min()
    assert stream_min == 0


def test_max() -> None:
    stream_max = Stream.range(0, 10).max()
    assert stream_max == 9


def test_split() -> None:
    stream_split = Stream.range(0, 10).split(lambda x: x % 2)
    assert str(stream_split) == "{0: <0, 2, 4, 6, 8>, 1: <1, 3, 5, 7, 9>}"
