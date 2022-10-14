from streams import Stream
from pytest import approx, raises


def test_case_1_first_15_odds() -> None:
    stream = Stream.counter().filter(lambda x: x % 2).stop(lambda x: x > 15)
    assert str(stream) == "<1, 3, 5, 7, 9, 11, 13, 15>"


def test_case_2_sum_powers_of_two() -> None:
    stream = Stream.counter().eval(lambda x: 1 / 2**x).limit(10_000).sum()
    assert stream == approx(2, 1e-4)


def test_case_3_triangular_summation() -> None:
    stream = Stream.counter().eval(lambda n: n * (n + 1) / 2).limit(20).sum()
    assert stream == 1330


def test_case_4_Ramanujan_summation() -> None:
    stream = Stream.counter().limit(10_000).sum()

    def summa() -> None:
        assert stream == -1 / 12

    raises(AssertionError, summa)


# def test_case_5_alphabet() -> None:
#     stream = Stream.range(65, 91).eval(chr).join()
#     assert stream == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def test_case_6_basel_problem() -> None:
    stream = Stream.counter(1).eval(lambda x: 1 / (x**2)).limit(10_000).sum()
    assert stream == approx(1.644934, abs=1e-4)


def test_case_7_Fibonacci_numbers() -> None:
    stream = Stream.fibonacci().limit(20).list()
    STREAM_RESULT = "[0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181]"
    assert str(stream) == STREAM_RESULT


def test_case_8_prime_numbers() -> None:
    stream = Stream.primes().stop(lambda x: x > 100).list()
    STREAM_RESULT = "[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]"
    assert str(stream) == STREAM_RESULT
