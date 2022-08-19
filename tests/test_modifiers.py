from streams import Stream


def test_filter() -> None:
    stream = Stream.range(20).filter(lambda x: x % 2, keep_if=True)
    assert str(stream) == "<1, 3, 5, 7, 9, 11, 13, 15, 17, 19>"


def test_slice() -> None:
    stream = Stream.range(20).slice(2, 11, 2)
    assert str(stream) == "<2, 4, 6, 8, 10>"


def test_skip() -> None:
    stream = Stream.range(20).skip(5)
    assert str(stream) == "<5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19>"


def test_limit() -> None:
    stream = Stream.range(20).limit(5)
    assert str(stream) == "<0, 1, 2, 3, 4>"


def test_stop() -> None:
    stream = Stream.range(20).stop(lambda x: x > 5)
    assert str(stream) == "<0, 1, 2, 3, 4, 5>"


def test_distinct() -> None:
    stream = Stream.repeat(1).limit(20).distinct()
    assert str(stream) == "<1>"


def test_enumerate() -> None:
    stream = Stream.range(2, 5, 1).enumerate()
    assert str(stream) == "<(0, 2), (1, 3), (2, 4)>"


def test_replace() -> None:
    stream = Stream.range(8).replace(5, 4)
    assert str(stream) == "<0, 1, 2, 3, 4, 4, 6, 7>"


def test_all_of_them() -> None:
    stream = (
        Stream.range(100)
        .filter(lambda x: x % 2)
        .slice(2, 40, 2)
        .skip(5)
        .limit(5)
        .distinct()
        .replace(15, -1)
        .enumerate()
    )
    assert str(stream) == "<(0, 25), (1, 29), (2, 33), (3, 37), (4, 41)>"
