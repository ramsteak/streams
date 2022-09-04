# streams
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![tests](https://github.com/ramsteak/streams/actions/workflows/black-tests.yml/badge.svg)](https://github.com/ramsteak/streams/actions/workflows/black-tests.yml)

## About
streams is a python library to use Java-like stream objects to manipulate an iterable collection lazily. In addition it offers elementwise exception handling.

## Installation

To install the latest release:
```sh
$ py -m pip install https://github.com/ramsteak/streams/releases/download/v1.0.0/streams-1.0.0-py3-none-any.whl
```
To install the most up-to-date changes:
```sh
$ py -m pip install git+https://github.com/ramsteak/streams.git
```

## Usage
```py
from streams import Stream

stream = (Stream.range(10)
            .filter(lambda x:x%2))

stream_list = stream.list()

>>> [1, 3, 5, 7, 9]
```

The stream object is able to catch exceptions at the item level without interrupting the stream, and the exceptions can be handled with the `.exc()` method.

```py
stream = (Stream.range(3)
            .eval(lambda x:1/x)
            .exc(ZeroDivisionError, 'replace', float('inf')))

stream_list = stream.list()

>>> [inf, 1.0, 0.5]
```
Unhandled exceptions will be raised after calling any other method.
```py
stream = (Stream.range(3)
            .eval(lambda x:1/x))
stream_list = stream.list()

>>> ZeroDivisionError: division by zero
```

See [test_use_cases.py](./tests/test_use_cases.py) for some examples.
