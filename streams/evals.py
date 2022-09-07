from typing import SupportsFloat, overload

__all__ = [
    'square',
    'cube'
]

@overload
def square(__x:float)->float:...
@overload
def square(__x:int)->int:...
@overload
def square(__x:SupportsFloat)->float:...
def square(__x):
    try:
        return pow(__x, 2)
    except TypeError:
        return pow(float(__x), 2)

@overload
def cube(__x:float)->float:...
@overload
def cube(__x:int)->int:...
@overload
def cube(__x:SupportsFloat)->float:...
def cube(__x):
    try:
        return pow(__x, 3)
    except TypeError:
        return pow(float(__x), 3)

