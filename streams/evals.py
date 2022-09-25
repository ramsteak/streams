from typing import Any, Callable, SupportsFloat, overload, TypeVar
import math

__all__ = [
    "square",
    "cube",
    "pow",
    "log",
    "root",
    "inv",
    "add",
    "radd",
    "sub",
    "rsub",
    "mul",
    "rmul",
    "div",
    "rdiv",
    "same",
    "lt",
    "le",
    "gt",
    "ge",
    "eq",
    "neq",
    "contains",
]

_T = TypeVar("_T")
_F = TypeVar("_F", float, SupportsFloat)


@overload
def square(__x: float) -> float:
    ...


@overload
def square(__x: int) -> int:
    ...


@overload
def square(__x: SupportsFloat) -> float:
    ...


def square(__x):
    try:
        return math.pow(__x, 2)
    except TypeError:
        return math.pow(float(__x), 2)


@overload
def cube(__x: float) -> float:
    ...


@overload
def cube(__x: int) -> int:
    ...


@overload
def cube(__x: _F) -> _F:
    ...


def cube(__x):
    try:
        return math.pow(__x, 3)
    except TypeError:
        return math.pow(float(__x), 3)


@overload
def pow(*, base: _F) -> Callable[[SupportsFloat], _F]:
    ...


@overload
def pow(*, exp: SupportsFloat) -> Callable[[_F], _F]:
    ...


def pow(**kw):
    if "base" in kw:
        base = kw["base"]

        def pow_b(exp: SupportsFloat) -> float:
            return math.pow(base, exp)

        return pow_b
    elif "exp" in kw:
        exp = kw["exp"]

        def pow_e(base: SupportsFloat) -> float:
            return math.pow(base, exp)

        return pow_e


@overload
def log(*, base: SupportsFloat) -> Callable[[_F], _F]:
    ...


@overload
def log(*, arg: _F) -> Callable[[SupportsFloat], _F]:
    ...


def log(**kw):
    if "base" in kw:
        base = kw["base"]

        def log_b(arg: SupportsFloat) -> float:
            return math.log(arg, base)

        return log_b
    if "arg" in kw:
        arg = kw["arg"]

        def log_a(base: SupportsFloat) -> float:
            return math.log(arg, base)

        return log_a


@overload
def root(*, deg: SupportsFloat) -> Callable[[_F], _F]:
    ...


@overload
def root(*, arg: _F) -> Callable[[SupportsFloat], _F]:
    ...


def root(**kw):
    if "deg" in kw:
        deg = kw["deg"]

        def root_d(arg: SupportsFloat) -> float:
            return math.pow(arg, 1.0 / deg)

        return root_d
    if "arg" in kw:
        arg = kw["arg"]

        def root_a(deg: SupportsFloat) -> float:
            return math.pow(arg, 1.0 / deg)

        return root_a


def inv(__x: _F) -> _F:
    return 1.0 / __x


def add(__v):
    def add_(__x: _T) -> _T:
        return __x.__add__(__v)

    return add_


def radd(__v):
    def add_(__x: _T) -> _T:
        return __x.__radd__(__v)

    return add_


def sub(__v):
    def sub_(__x: _T) -> _T:
        return __x.__sub__(__v)

    return sub_


def rsub(__v):
    def sub_(__x: _T) -> _T:
        return __x.__rsub__(__v)

    return sub_


def mul(__v):
    def mul_(__x: _T) -> _T:
        return __x.__mul__(__v)

    return mul_


def rmul(__v):
    def mul_(__x: _T) -> _T:
        return __x.__rmul__(__v)

    return mul_


def div(__v):
    def div_(__x: _T) -> _T:
        return __x.__truediv__(__v)

    return div_


def rdiv(__v):
    def div_(__x: _T) -> _T:
        return __x.__rtruediv__(__v)

    return div_


def same(__v: _T) -> _T:
    return __v


def lt(__v: _T):
    def lt_(__x: _T) -> bool:
        return __x.__lt__(__v)

    return lt_


def le(__v: _T):
    def le_(__x: _T) -> bool:
        return __x.__le__(__v)

    return le_


def gt(__v: _T):
    def gt_(__x: _T) -> bool:
        return __x.__gt__(__v)

    return gt_


def ge(__v: _T):
    def ge_(__x: _T) -> bool:
        return __x.__ge__(__v)

    return ge_


def eq(__v: _T):
    def eq_(__x: _T) -> bool:
        return __x.__eq__(__v)

    return eq_


def neq(__v: _T):
    def neq_(__x: _T) -> bool:
        return not (__x.__eq__(__v))

    return neq_


def contains(__v: _T):
    def cont_(__x: dict[_T, Any]) -> bool:
        return __v in __x

    return cont_
