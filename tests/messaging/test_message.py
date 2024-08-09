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

from ocr_translate.messaging import Message

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


def test_message_instantiation(message, handler):
    """Test that the message class can be instantiated"""
    assert isinstance(message, Message)
    assert message.id_ == ()
    assert message.msg == {'args': (), 'kwargs': {}}
    assert message.handler == handler

def test_message_eq(message):
    """Test that the message class __eq__ method works"""
    assert message == message # pylint: disable=comparison-with-itself

def test_message_ne_same(message):
    """Test that the message class __ne__ method works"""
    message1 = message.copy()
    message2 = message.copy()
    message2.msg['args'] = (1,2,3)
    assert message1 != message2

def test_message_ne_different(message):
    """Test that the message class __ne__ method works"""
    assert message != 'test'

@pytest.mark.parametrize('handler', ['raise'], indirect=True)
def test_message_resolve_exception(message):
    """Test exception handling in the message resolve method."""
    assert not message.is_resolved
    message.resolve()
    res = message.response()
    assert isinstance(res, Exception)
    assert res.args == ('Test exception',)

def test_message_resolve(message):
    """Test that the message class can be resolved"""
    assert not message.is_resolved
    message.resolve()
    assert message.is_resolved
    assert message.response() == ((), {})

def test_message_batch_resolve_different_handler(message):
    """Test that batch_resolve raises ValueError if the handler is different"""
    message1 = message.copy()
    message2 = message.copy()
    message2.handler = lambda *args, **kwargs: (args, kwargs)

    with pytest.raises(ValueError, match=r'.*same handler$'):
        message1.batch_resolve([message2])

def test_message_batch_resolve_different_args(message):
    """Test that batch_resolve raises ValueError if the number of args is different for any message"""
    message1 = message.copy()
    message2 = message.copy()
    message2.msg['args'] = (1,2,3)

    with pytest.raises(ValueError, match=r'.*same number of args$'):
        message1.batch_resolve([message2])

    message3 = message.copy()
    with pytest.raises(ValueError, match=r'.*same number of args$'):
        message1.batch_resolve([message3,message2])


def test_message_batch_resolve_different_kwargs(message):
    """Test that batch_resolve raises ValueError if the keys of the kwargs are different for any message"""
    message1 = message.copy()
    message2 = message.copy()
    message2.msg['kwargs'] = {'kw1': 1, 'kw3': 3}

    with pytest.raises(ValueError, match=r'.*same kwargs$'):
        message1.batch_resolve([message2])

    message3 = message.copy()
    with pytest.raises(ValueError, match=r'.*same kwargs$'):
        message1.batch_resolve([message3,message2])

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
@pytest.mark.parametrize('num_msg', [2,3], ids=['num_msg=2', 'num_msg=3'])
def test_message_batch_resolve(batch_message, num_msg):
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

def test_message_delete_data(message):
    """Test that the message class can be resolved"""
    assert message.msg
    message.resolve()
    with pytest.raises(AttributeError):
        getattr(message, 'msg')

def test_messate_timeout(message):
    """Test that the message class can be resolved"""
    with pytest.raises(TimeoutError):
        message.response(timeout=0.01)

@pytest.mark.parametrize('message', msg_list, indirect=True)
def test_message_args(message):
    """Test that the message class can be resolved"""
    assert not message.is_resolved
    args = message.msg.get('args', ())
    kwargs = message.msg.get('kwargs', {})
    message.resolve()
    assert message.is_resolved
    assert message.response() == (args, kwargs)
