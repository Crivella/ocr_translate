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

from ocr_translate.messaging import Worker, WorkerMessageQueue


def test_wmq_instantiation(worker_message_queue):
    """Test that the worker message queue class can be instantiated"""
    assert isinstance(worker_message_queue, WorkerMessageQueue)
    assert isinstance(worker_message_queue.msg_queue, queue.SimpleQueue)
    for worker in worker_message_queue.workers:
        assert isinstance(worker, Worker)

@pytest.mark.parametrize('worker_message_queue', [1,2], ids=['num_workers=1', 'num_workers=2'], indirect=True)
def test_wmq_start(worker_message_queue):
    """Test that all workers are being started"""
    for worker in worker_message_queue.workers:
        assert worker.thread is None
    worker_message_queue.start_workers()
    for worker in worker_message_queue.workers:
        assert isinstance(worker.thread, threading.Thread)
        assert worker.thread.is_alive()

@pytest.mark.parametrize('worker_message_queue', [1,2], ids=['num_workers=1', 'num_workers=2'], indirect=True)
def test_wmq_stop(worker_message_queue):
    """Test that all workers are being stopped"""
    worker_message_queue.start_workers()
    worker_message_queue.stop_workers()
    for worker in worker_message_queue.workers:
        assert not worker.thread.is_alive()

def test_wmq_put(worker_message_queue, message):
    """Test that a message can be put into the queue"""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    assert worker_message_queue.msg_queue.empty()
    worker_message_queue.put(id_=id_, msg=msg, handler=handler)
    assert not worker_message_queue.msg_queue.empty()

def test_wmq_get(worker_message_queue, message):
    """Test that a message can be put and retreived from the queue"""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    new_msg = worker_message_queue.put(id_=id_, msg=msg, handler=handler)
    assert worker_message_queue.get() is new_msg
    assert worker_message_queue.msg_queue.empty()

def test_wmq_get_msg(worker_message_queue, message):
    """Test get_msg when reuse_msg is True (default)."""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    new_msg = worker_message_queue.put(id_=id_, msg=msg, handler=handler)
    assert worker_message_queue.get_msg(id_) is new_msg

def test_worker_many(worker_message_queue, message):
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
        [
            {'id_': 0, 'msg': {'args': (1,2)}, 'batch_args': (0,)},
            {'id_': 0,'msg':{'kwargs': {'kw1': 1, 'kw2': 2}}, 'batch_kwargs': ('kw1',)},
        ],
        ids=['ba0', 'bkw1'],
        indirect=True
        )
@pytest.mark.parametrize('num_msg', [1,10], ids=['num_msg=1', 'num_msg=10'])
def test_worker_batch_resolve(batched_worker_message_queue, batch_message, num_msg):
    """Test that the worker class can be stopped"""
    batched_worker_message_queue.start_workers()
    msg = batch_message.msg
    args = msg.get('args', ())
    kwargs = msg.get('kwargs', {})
    handler = batch_message.handler
    messages = [
        batched_worker_message_queue.put(id_=i, msg=msg, handler=handler, batch_id=0) for i in range(num_msg)
        ]

    for message in messages:
        assert message.response(timeout=1.0) == (args, kwargs)
    batched_worker_message_queue.stop_workers()
