import math
from streams import Stream
from streams.evals import *

def test_square():
    s = Stream.fibonacci().eval(square).limit(10).sum()
    assert s == 1870

def test_cube():
    s = Stream.fibonacci().eval(cube).limit(10).sum()
    assert s == 51436

math