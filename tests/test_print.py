from streams import Stream
from pytest import CaptureFixture


def test_print_1(capsys: CaptureFixture) -> None:
    _ = Stream.range(10).stop(lambda x: x > 5).print().null()
    out, _ = capsys.readouterr()
    assert out == "<0, 1, 2, 3, 4, 5>\n"


def test_print_2(capsys: CaptureFixture) -> None:
    _ = Stream.range(10).print().stop(lambda x: x > 5).null()
    out, _ = capsys.readouterr()
    assert out == "<0, 1, 2, 3, 4, 5, 6, ...>\n"


def test_print_3(capsys: CaptureFixture) -> None:
    # At first glance it looks like an error, but it is necessary for stop to get
    # the next item, so it gets called for print
    _ = Stream.range(10).print().stop(lambda x: x > 5, inclusive=True).null()
    out, _ = capsys.readouterr()
    assert out == "<0, 1, 2, 3, 4, 5, 6, ...>\n"
