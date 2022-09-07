from streams import Stream
from streams.evals import *


def test_square():
    s = Stream.fibonacci().eval(square).limit(10).sum()
    assert s == 1870


def test_cube():
    s = Stream.fibonacci().eval(cube).limit(10).sum()
    assert s == 51436


def test_pow():
    s = Stream.range(5).eval(pow(base=2))
    assert str(s) == "<1.0, 2.0, 4.0, 8.0, 16.0>"
    s = Stream.range(5).eval(pow(exp=2))
    assert str(s) == "<0.0, 1.0, 4.0, 9.0, 16.0>"


def test_log():
    s = Stream.range(1, 4).eval(log(base=2))
    assert str(s) == "<0.0, 1.0, 1.5849625007211563>"
    s = Stream.range(2, 4).eval(log(arg=2))
    assert str(s) == "<1.0, 0.6309297535714574>"


def test_root():
    s = Stream.range(3).eval(root(deg=2))
    assert str(s) == "<0.0, 1.0, 1.4142135623730951>"
    s = Stream.range(1, 3).eval(root(arg=2))
    assert str(s) == "<2.0, 1.4142135623730951>"


def test_inv():
    s = Stream.range(1, 3).eval(inv)
    assert str(s) == "<1.0, 0.5>"


def test_add():
    s = Stream.range(5).eval(add(1))
    assert str(s) == "<1, 2, 3, 4, 5>"
    s = Stream.range(5).eval(radd(1))
    assert str(s) == "<1, 2, 3, 4, 5>"


def test_sub():
    s = Stream.range(5).eval(sub(1))
    assert str(s) == "<-1, 0, 1, 2, 3>"
    s = Stream.range(5).eval(rsub(1))
    assert str(s) == "<1, 0, -1, -2, -3>"


def test_mul():
    s = Stream.range(5).eval(mul(2))
    assert str(s) == "<0, 2, 4, 6, 8>"
    s = Stream.range(5).eval(rmul(2))
    assert str(s) == "<0, 2, 4, 6, 8>"


def test_div():
    s = Stream.range(5).eval(div(2))
    assert str(s) == "<0.0, 0.5, 1.0, 1.5, 2.0>"
    s = Stream.range(1, 5).eval(rdiv(2))
    assert str(s) == "<2.0, 1.0, 0.6666666666666666, 0.5>"


def test_same():
    s = Stream.range(5).eval(same)
    assert str(s) == "<0, 1, 2, 3, 4>"
