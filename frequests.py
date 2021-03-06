# -*- coding: utf-8 -*-

"""
frequests
~~~~~~~~~

This module contains an asynchronous replica of ``requests.api``, powered
by futures. All API methods return a ``Request`` instance (as opposed to
``Response``). A list of requests can be sent with ``map()``.
"""

import sys
from functools import partial

try:
    from concurrent.futures import ThreadPoolExecutor  # this works in python 3.X and newer version of futures in python 2.X
except ImportError:
    if sys.version_info[0] == 2:
        try:
            from futures import ThreadPoolExecutor  # for older versions of futures in python 2.x
        except ImportError:
            raise RuntimeError('futures is required for frequests on python 2.X')

try:
    from requests import Session
except ImportError:
    raise RuntimeError('requests is required for frequests')


__all__ = (
    'map', 'imap',
    'get', 'options', 'head', 'post', 'put', 'patch', 'delete', 'request'
)


class AsyncRequest(object):
    """ Asynchronous request.

    Accept same parameters as ``Session.request`` and some additional:

    :param session: Session which will do request
    :param callback: Callback called on response.
    Same as passing ``hooks={'response': callback}``
    """
    def __init__(self, method, url, **kwargs):
        #: Request method
        self.method = method
        #: URL to request
        self.url = url
        #: Associated ``Session``
        self.session = kwargs.pop('session', None)
        if self.session is None:
            self.session = Session()

        callback = kwargs.pop('callback', None)
        if callback:
            kwargs['hooks'] = {'response': callback}

        #: The rest arguments for ``Session.request``
        self.kwargs = kwargs
        #: Resulting ``Response``
        self.response = None

    def send(self, **kwargs):
        """
        Prepares request based on parameter passed to constructor and optional ``kwargs```.
        Then sends request and saves response to :attr:`response`

        :returns: ``Response``
        """
        merged_kwargs = {}
        merged_kwargs.update(self.kwargs)
        merged_kwargs.update(kwargs)
        self.response = self.session.request(self.method,
                                              self.url, **merged_kwargs)
        return self.response

def send(r, stream=False):
    """Just sends the request using its send method and returns its response.  """
    r.send(stream=stream)
    return r.response

# Shortcuts for creating AsyncRequest with appropriate HTTP method
get = partial(AsyncRequest, 'GET')
options = partial(AsyncRequest, 'OPTIONS')
head = partial(AsyncRequest, 'HEAD')
post = partial(AsyncRequest, 'POST')
put = partial(AsyncRequest, 'PUT')
patch = partial(AsyncRequest, 'PATCH')
delete = partial(AsyncRequest, 'DELETE')

# synonym
def request(method, url, **kwargs):
    return AsyncRequest(method, url, **kwargs)

def map(requests, stream=True, size=1, **kwargs):
    """Concurrently converts a list of Requests to Responses.

    :param requests: a collection of Request objects.
    :param stream: If False, the content will not be downloaded immediately.
    :param size: Specifies the number of requests to make at a time. If 1, no throttling occurs.
    """

    requests = list(requests)

    with ThreadPoolExecutor(max_workers=size) as executor:
        responses = list(executor.map(send, requests, [stream]*len(requests), **kwargs))

    return responses

def imap(requests, stream=True, size=2, **kwargs):
    """Concurrently converts a generator object of Requests to
    a generator of Responses.

    :param requests: a generator of Request objects.
    :param stream: If False, the content will not be downloaded immediately.
    :param size: Specifies the number of requests to make at a time. default is 2
    """

    def stream():
        while True:
            yield stream

    with ThreadPoolExecutor(max_workers=size) as executor:
        for response in executor.map(send, requests, stream(), **kwargs):
            yield response
