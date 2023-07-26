###################################################################################
# ocr_translate - a django app to perform OCR and translation of images.          #
# Copyright (C) 2023-present Davide Grassano                                      #
#                                                                                 #
# This program is free software: you can redistribute it and/or modify            #
# it under the terms of the GNU General Public License as published by            #
# the Free Software Foundation, either version 3 of the License.                  #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program.  If not, see {http://www.gnu.org/licenses/}.           #
#                                                                                 #
# Home: https://github.com/Crivella/ocr_translate                                 #
###################################################################################
"""Tests for messaging.py"""
# pylint: disable=redefined-outer-name

import queue
import threading

import pytest

from ocr_translate.messaging import (Message, MessageQueue, Worker,
                                     WorkerMessageQueue)

msg_list = [
    {
        'args': (
            'test_arg1',
        )
    },
    {
        'args': (
            'test_arg1',
            'test_arg2'
        )
    },
    {
        'args': (
            'test_arg1',
            'test_arg2',
        ),
        'kwargs': {
            'test_key1': 'test_value1'
        }
    },
    {
        'args': (
            'test_arg1',
            'test_arg2',
        ),
        'kwargs': {
            'test_key1': 'test_value1',
            'test_key2': 'test_value2'
        }
    },
    {
        'kwargs': {
            'test_key1': 'test_value1',
            'test_key2': 'test_value2'
        }
    },
]

class TestMessage():
    """Test the Message class"""

    def test_message_instantiation(self, message, handler):
        """Test that the message class can be instantiated"""
        assert isinstance(message, Message)
        assert message.id_ == ()
        assert message.msg == {'args:': (), 'kwargs': {}}
        assert message.handler == handler

    def test_message_eq(self, message):
        """Test that the message class __eq__ method works"""
        assert message == message # pylint: disable=comparison-with-itself

    def test_message_resolve(self, message):
        """Test that the message class can be resolved"""
        assert not message.is_resolved
        message.resolve()
        assert message.is_resolved
        assert message.response() == ((), {})

    @pytest.mark.parametrize(
            'batch_message',
            [
                {'id_': 0,'msg':{'args': (1,2)}, 'batch_args': (0,)},
                {'id_': 0,'msg':{'args': (1,2)}, 'batch_args': (1,)},
                {'id_': 0,'msg':{'kwargs': {'kw1': 1, 'kw2': 2}}, 'batch_kwargs': ('kw1',)},
                {'id_': 0,'msg':{'kwargs': {'kw1': 1, 'kw2': 2}}, 'batch_kwargs': ('kw2',)},
                {'id_': 0,'msg':{
                    'args':(0,1),
                    'kwargs': {'kw1': 1, 'kw2': 2}},
                    'batch_args': (0,),
                    'batch_kwargs': ('kw2',)},
            ],
            ids=['ba0', 'ba1', 'bkw1', 'bkw2', 'ba0+bkw2'],
            indirect=True
            )
    @pytest.mark.parametrize('num_msg', [2,3], ids=['num_msg=1', 'num_msg=2'])
    def test_message_batch_resolve(self, batch_message, num_msg):
        """Test batch resolve of multiple messages"""

        messages = []
        msg_res = []
        for i in range(num_msg):
            new_msg = batch_message.copy()
            args = list(new_msg.msg.get('args', ()))
            for j in new_msg.batch_args:
                args[j] += i
            new_msg.msg['args'] = tuple(args)
            for k in new_msg.batch_kwargs:
                new_msg.msg['kwargs'][k] += i

            messages.append(new_msg)
            msg_res.append((new_msg.msg['args'], new_msg.msg['kwargs']))

        messages[0].batch_resolve(messages[1:])

        for msg, expected in zip(messages, msg_res):
            assert msg.is_resolved
            assert msg.response() == expected

    def test_message_delete_data(self, message):
        """Test that the message class can be resolved"""
        assert message.msg
        message.resolve()
        with pytest.raises(AttributeError):
            getattr(message, 'msg')

    def test_messate_timeout(self, message):
        """Test that the message class can be resolved"""
        with pytest.raises(TimeoutError):
            message.response(timeout=0.01)

    @pytest.mark.parametrize('message', msg_list, indirect=True)
    def test_message_args(self, message):
        """Test that the message class can be resolved"""
        assert not message.is_resolved
        args = message.msg.get('args', ())
        kwargs = message.msg.get('kwargs', {})
        message.resolve()
        assert message.is_resolved
        assert message.response() == (args, kwargs)

class TestMessageQueue():
    """Test the MessageQueue class"""

    def test_queue_instantiation(self, message_queue):
        """Test that the message queue class can be instantiated"""
        assert isinstance(message_queue, MessageQueue)
        assert message_queue.empty()


    def test_queue_put(self, message_queue, message):
        """Test that a message can be put into the queue"""
        id_ = message.id_
        msg = message.msg
        handler = message.handler
        message_queue.put(id_=id_, msg=msg, handler=handler)
        assert not message_queue.empty()

    def test_queue_get(self, message_queue, message):
        """Test that a message can be put into the queue"""
        id_ = message.id_
        msg = message.msg
        handler = message.handler
        new_msg = message_queue.put(id_=id_, msg=msg, handler=handler)
        assert message_queue.get() is new_msg
        assert message_queue.empty()

    def test_queue_get_msg(self, message_queue, message):
        """Test get_msg when reuse_msg is True (default)."""
        id_ = message.id_
        msg = message.msg
        handler = message.handler
        new_msg = message_queue.put(id_=id_, msg=msg, handler=handler)
        assert message_queue.get_msg(id_) is new_msg

    def test_queue_put_same_msg(self, message_queue, message):
        """Test putting the same message into the queue. The default behavior should be to return
        the already queued message."""
        id_ = message.id_
        msg = message.msg
        handler = message.handler
        new_msg1 = message_queue.put(id_=id_, msg=msg, handler=handler)
        new_msg2 = message_queue.put(id_=id_, msg=msg, handler=handler)
        assert new_msg1 is new_msg2

    def test_queue_put_batch_msg(self, message_queue, message):
        """Test putting batch message into the queue. By default batching is desabled
        and this should return ValueError."""
        id_ = message.id_
        msg = message.msg
        handler = message.handler
        with pytest.raises(ValueError):
            message_queue.put(id_=id_, msg=msg, handler=handler, batch_id=0)

    def test_nocache_queue_get_msg(self, nocache_queue, message):
        """Test get_msg when reuse_msg is False."""
        id_ = message.id_
        msg = message.msg
        handler = message.handler
        nocache_queue.put(id_=id_, msg=msg, handler=handler)
        with pytest.raises(ValueError):
            nocache_queue.get_msg(id_)

    def test_batch_queue_instantiation_fail(self):
        """Test creating batched queue raises ValueError if neither batch_args or batch_kwargs is specified."""
        with pytest.raises(ValueError):
            MessageQueue(allow_batching=True)

    def test_batch_queue_instantiation(self, batched_queue):
        """Test creating batched queue."""
        assert isinstance(batched_queue, MessageQueue)
        assert batched_queue.allow_batching is True

    def test_batch_queue_put(self, batched_queue, message):
        """Test that a message are grouped into pools defined by the batch_id"""
        msg = message.msg
        handler = message.handler
        batch_id = 0
        new_msg1 = batched_queue.put(id_=0, msg=msg, handler=handler, batch_id=batch_id)
        new_msg2 = batched_queue.put(id_=1, msg=msg, handler=handler, batch_id=batch_id)
        assert new_msg1 in batched_queue.batch_pools[batch_id]
        assert new_msg2 in batched_queue.batch_pools[batch_id]

    @pytest.mark.parametrize('num_msg', [1,2], ids=['num_msg=1', 'num_msg=2'])
    def test_batch_queue_get_multiple(self, batched_queue, message, num_msg):
        """Test that a message can be put into the queue"""
        msg = message.msg
        handler = message.handler
        batch_id = 0
        messages = []
        for i in range(num_msg):
            new = batched_queue.put(id_=i, msg=msg, handler=handler, batch_id=batch_id)
            messages.append(new)

        res = batched_queue.get()
        assert isinstance(res, list)
        assert len(res) == num_msg
        for msg in messages:
            assert msg in res


class TestWorker():
    """Test the Worker class"""

    def test_worker_instantiation(self, worker):
        """Test that the worker class can be instantiated"""
        assert isinstance(worker, Worker)
        assert isinstance(worker.queue, queue.SimpleQueue)

    def test_worker_start(self, worker):
        """Test that the worker class can be started"""
        assert worker.thread is None
        worker.start()
        assert isinstance(worker.thread, threading.Thread)
        assert worker.thread.is_alive()

    def test_worker_stop(self, worker):
        """Test that the worker class can be stopped"""
        worker.start()
        worker.stop()
        assert not worker.thread.is_alive()

class TestWorkerMessageQueue():
    """Test the WorkerMessageQueue class"""

    def test_wmq_instantiation(self, worker_message_queue):
        """Test that the worker message queue class can be instantiated"""
        assert isinstance(worker_message_queue, WorkerMessageQueue)
        assert isinstance(worker_message_queue.msg_queue, queue.SimpleQueue)
        for worker in worker_message_queue.workers:
            assert isinstance(worker, Worker)

    @pytest.mark.parametrize('worker_message_queue', [1,2], ids=['num_workers=1', 'num_workers=2'], indirect=True)
    def test_wmq_start(self, worker_message_queue):
        """Test that all workers are being started"""
        for worker in worker_message_queue.workers:
            assert worker.thread is None
        worker_message_queue.start_workers()
        for worker in worker_message_queue.workers:
            assert isinstance(worker.thread, threading.Thread)
            assert worker.thread.is_alive()

    @pytest.mark.parametrize('worker_message_queue', [1,2], ids=['num_workers=1', 'num_workers=2'], indirect=True)
    def test_wmq_stop(self, worker_message_queue):
        """Test that all workers are being stopped"""
        worker_message_queue.start_workers()
        worker_message_queue.stop_workers()
        for worker in worker_message_queue.workers:
            assert not worker.thread.is_alive()

    def test_wmq_put(self, worker_message_queue, message):
        """Test that a message can be put into the queue"""
        id_ = message.id_
        msg = message.msg
        handler = message.handler
        assert worker_message_queue.msg_queue.empty()
        worker_message_queue.put(id_=id_, msg=msg, handler=handler)
        assert not worker_message_queue.msg_queue.empty()

    def test_wmq_get(self, worker_message_queue, message):
        """Test that a message can be put and retreived from the queue"""
        id_ = message.id_
        msg = message.msg
        handler = message.handler
        new_msg = worker_message_queue.put(id_=id_, msg=msg, handler=handler)
        assert worker_message_queue.get() is new_msg
        assert worker_message_queue.msg_queue.empty()

    def test_worker_many(self, worker_message_queue, message):
        """Test that a message can be put into the queue"""
        worker_message_queue.start_workers()
        msg = message.msg
        handler = message.handler
        messages = [worker_message_queue.put(id_=i, msg=msg, handler=handler) for i in range(10)]
        for _ in messages:
            assert _.response(timeout=1.0) == ((), {})
        worker_message_queue.stop_workers()

    @pytest.mark.parametrize(
            'batch_message',
            [{'id_': 0, 'msg': {'args': (1,2)}, 'batch_args': (0,)}],
            indirect=True
            )
    def test_worker_batch_resolve(self, batched_worker_message_queue, batch_message):
        """Test that the worker class can be stopped"""
        batched_worker_message_queue.start_workers()
        msg = batch_message.msg
        args = msg.get('args', ())
        kwargs = msg.get('kwargs', {})
        handler = batch_message.handler
        messages = [batched_worker_message_queue.put(id_=i, msg=msg, handler=handler, batch_id=0) for i in range(10)]

        for message in messages:
            assert message.response(timeout=1.0) == (args, kwargs)
        batched_worker_message_queue.stop_workers()
