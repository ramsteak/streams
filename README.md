# streams
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![tests](https://github.com/ramsteak/streams/actions/workflows/black-tests.yml/badge.svg)](https://github.com/ramsteak/streams/actions/workflows/black-tests.yml)

## About
streams is a python library to use Java-like stream objects to manipulate an iterable collection lazily. In addition it offers elementwise exception handling.

## Usage
To use the package (not yet in pypi) you have to install directly from github.

```py
from streams import Stream

stream = (Stream
            .range(6)
            .filter(lambda x:x%2))

stream_list = stream.list()

>>> [1, 3, 5]
```

The stream object is able to catch exceptions at the item level without interrupting the stream, and the exceptions can be handled with the `.exc()` method.

```py
stream = (Stream
            .range(3)
            .eval(lambda x:1/x)
            .exc(ZeroDivisionError, 'replace', float('inf')))

stream_list = stream.list()

>>> [inf, 1.0, 0.5]
```