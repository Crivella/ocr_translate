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

import pytest

from ocr_translate.messaging import MessageQueue


def test_queue_instantiation(message_queue):
    """Test that the message queue class can be instantiated"""
    assert isinstance(message_queue, MessageQueue)
    assert message_queue.empty()


def test_queue_put(message_queue, message):
    """Test that a message can be put into the queue"""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    message_queue.put(id_=id_, msg=msg, handler=handler)
    assert not message_queue.empty()

def test_queue_get(message_queue, message):
    """Test that a message can be put into the queue"""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    new_msg = message_queue.put(id_=id_, msg=msg, handler=handler)
    assert message_queue.get() is new_msg
    assert message_queue.empty()

def test_queue_get_msg(message_queue, message):
    """Test get_msg when reuse_msg is True (default)."""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    new_msg = message_queue.put(id_=id_, msg=msg, handler=handler)
    assert message_queue.get_msg(id_) is new_msg

def test_queue_put_same_msg(message_queue, message):
    """Test putting the same message into the queue. The default behavior should be to return
    the already queued message."""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    new_msg1 = message_queue.put(id_=id_, msg=msg, handler=handler)
    new_msg2 = message_queue.put(id_=id_, msg=msg, handler=handler)
    assert new_msg1 is new_msg2

def test_queue_put_batch_msg(message_queue, message):
    """Test putting batch message into the queue. By default batching is desabled
    and this should return ValueError."""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    with pytest.raises(ValueError):
        message_queue.put(id_=id_, msg=msg, handler=handler, batch_id=0)

def test_nocache_queue_get_msg(nocache_queue, message):
    """Test get_msg when reuse_msg is False."""
    id_ = message.id_
    msg = message.msg
    handler = message.handler
    nocache_queue.put(id_=id_, msg=msg, handler=handler)
    with pytest.raises(ValueError):
        nocache_queue.get_msg(id_)

def test_batch_queue_instantiation_fail():
    """Test creating batched queue raises ValueError if neither batch_args or batch_kwargs is specified."""
    with pytest.raises(ValueError):
        MessageQueue(allow_batching=True)

def test_batch_queue_instantiation(batched_queue):
    """Test creating batched queue."""
    assert isinstance(batched_queue, MessageQueue)
    assert batched_queue.allow_batching is True

def test_batch_queue_put(batched_queue, message):
    """Test that a message are grouped into pools defined by the batch_id"""
    msg = message.msg
    handler = message.handler
    batch_id = 0
    new_msg1 = batched_queue.put(id_=0, msg=msg, handler=handler, batch_id=batch_id)
    new_msg2 = batched_queue.put(id_=1, msg=msg, handler=handler, batch_id=batch_id)
    assert new_msg1 in batched_queue.batch_pools[batch_id]
    assert new_msg2 in batched_queue.batch_pools[batch_id]

@pytest.mark.parametrize('num_msg', [1,2], ids=['num_msg=1', 'num_msg=2'])
def test_batch_queue_get_multiple(batched_queue, message, num_msg):
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
