"""Fixtures for messaging tests"""
# pylint: disable=redefined-outer-name

import pytest

from ocr_translate.messaging import (Message, MessageQueue, Worker,
                                     WorkerMessageQueue)


@pytest.fixture
def handler(request):
    """Return a simple handler function"""
    def _handler(*args, **kwargs):
        if hasattr(request, 'param') and request.param == 'raise':
            raise Exception('Test exception') # pylint: disable=broad-exception-raised
        return args, kwargs

    return _handler

@pytest.fixture()
def message(request, handler):
    """Return a simple message"""
    id_ = ()
    msg = {'args': (), 'kwargs': {}}
    if hasattr(request, 'param'):
        msg = request.param
        args = msg.get('args', ())
        kwargs = msg.get('kwargs', {})
        id_ = (args, kwargs)

    return Message(id_=id_, msg=msg, handler=handler)

@pytest.fixture()
def batch_message(request):
    """Return a batched message"""
    data = request.param
    msg = data.setdefault('msg', {})
    msg.setdefault('args', ())
    msg.setdefault('kwargs', {})
    batch_args = data.setdefault('batch_args', ())
    batch_kwargs = data.setdefault('batch_kwargs', {})

    def _handler(*args, **kwargs):
        """Generic handler for batched messages."""
        try:
            if batch_args:
                bsize = len(args[batch_args[0]])
            elif batch_kwargs:
                bsize = len(kwargs[batch_kwargs[0]])
            else:
                bsize = 1
        except TypeError:
            # Batch handler are supposed to work also with non-batched messages
            return args, kwargs
        res = []
        for i in range(bsize):
            res_args = tuple(arg[i] if j in batch_args else arg for j,arg in enumerate(args))
            res_kwargs = {k: v[i] if k in batch_kwargs else v for k,v in kwargs.items()}
            res.append((res_args, res_kwargs))

        return res
    return Message(**data, handler=_handler)

@pytest.fixture()
def message_queue(request):
    """Return a message queue"""
    args = ()
    kwargs = {}
    if hasattr(request, 'param'):
        args, kwargs = request.param
    return MessageQueue(*args, **kwargs)

@pytest.fixture()
def nocache_queue():
    """Return a message queue with no cache"""
    return MessageQueue(reuse_msg=0)

@pytest.fixture(params=[((0,), {})], ids=['batch_arg0'])
def batched_queue(request):
    """Return a message queue with a batch size of 2"""
    args, kwargs = request.param

    return MessageQueue(allow_batching=True, batch_args=args, batch_kwargs=kwargs)

@pytest.fixture()
def worker(message_queue):
    """Return a worker"""
    return Worker(message_queue)

@pytest.fixture()
def worker_message_queue():
    """Return a worker message queue"""
    return WorkerMessageQueue()

@pytest.fixture()
def batched_worker_message_queue(batch_message):
    """Return a worker message queue"""
    # Chanced for testing with differend batch args/kwargs
    return WorkerMessageQueue(
        allow_batching=True,
        batch_args=batch_message.batch_args,
        batch_kwargs=batch_message.batch_kwargs
        )
