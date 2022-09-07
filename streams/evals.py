from typing import Callable, SupportsFloat, overload, TypeVar 
import math

__all__ = [
    'square',
    'cube',
    'pow',
    'log',
    'root',
    'inv',
    'add',
    'radd',
    'sub',
    'rsub',
    'mul',
    'rmul',
    'div',
    'rdiv',
    'same'
]

_T = TypeVar("_T")

@overload
def square(__x:float) -> float:...
@overload
def square(__x:int) -> int:...
@overload
def square(__x:SupportsFloat) -> float:...
def square(__x):
    try:
        return math.pow(__x, 2)
    except TypeError:
        return math.pow(float(__x), 2)

@overload
def cube(__x:float) -> float:...
@overload
def cube(__x:int) -> int:...
@overload
def cube(__x:SupportsFloat) -> float:...
def cube(__x):
    try:
        return math.pow(__x, 3)
    except TypeError:
        return math.pow(float(__x), 3)


@overload
def pow(*,base:SupportsFloat) -> Callable[[SupportsFloat], float]:...
@overload
def pow(*,exp:SupportsFloat) -> Callable[[SupportsFloat], float]:...
def pow(**kw):
    if 'base' in kw:
        base = kw['base']
        def pow_b(exp:SupportsFloat) -> float:
            return math.pow(base, exp)
        return pow_b
    elif 'exp' in kw:
        exp = kw['exp']
        def pow_e(base:SupportsFloat) -> float:
            return math.pow(base, exp)
        return pow_e

@overload
def log(*,base:SupportsFloat) -> Callable[[SupportsFloat], float]:...
@overload
def log(*,arg:SupportsFloat) -> Callable[[SupportsFloat], float]:...
def log(**kw):
    if 'base' in kw:
        base = kw['base']
        def log_b(arg:SupportsFloat) -> float:
            return math.log(arg, base)
        return log_b
    if 'arg' in kw:
        arg = kw['arg']
        def log_a(base:SupportsFloat) -> float:
            return math.log(arg, base)
        return log_a


@overload
def root(*, deg:SupportsFloat) -> Callable[[SupportsFloat], float]:...
@overload
def root(*, arg:SupportsFloat) -> Callable[[SupportsFloat], float]:...
def root(**kw):
    if 'deg' in kw:
        deg = kw['deg']
        def root_d(arg:SupportsFloat) -> float:
            return math.pow(arg, 1.0/deg)
        return root_d
    if 'arg' in kw:
        arg = kw['arg']
        def root_a(deg:SupportsFloat) -> float:
            return math.pow(arg, 1.0/deg)
        return root_a

def inv(__x:SupportsFloat) -> float:
    return 1.0/__x


def add(__v):
    def add_(__x:_T) -> _T:
        return __x.__add__(__v)
    return add_

def radd(__v):
    def add_(__x:_T) -> _T:
        return __x.__radd__(__v)
    return add_

def sub(__v):
    def sub_(__x:_T) -> _T:
        return __x.__sub__(__v)
    return sub_

def rsub(__v):
    def sub_(__x:_T) -> _T:
        return __x.__rsub__(__v)
    return sub_

def mul(__v):
    def mul_(__x:_T) -> _T:
        return __x.__mul__(__v)
    return mul_

def rmul(__v):
    def mul_(__x:_T) -> _T:
        return __x.__rmul__(__v)
    return mul_

def div(__v):
    def div_(__x:_T) -> _T:
        return __x.__truediv__(__v)
    return div_

def rdiv(__v):
    def div_(__x:_T) -> _T:
        return __x.__rtruediv__(__v)
    return div_

def same(__v:_T) -> _T:
    return __v