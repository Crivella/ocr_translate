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
"""Tests for translation module."""

import pytest

from ocr_translate import models as m
from ocr_translate.messaging import Message
from ocr_translate.ocr_tsl import tsl

tsl_globals = ['TSL_MODEL', 'TSL_TOKENIZER', 'TSL_MODEL_OBJ']

def test_get_mnt_wrong_options():
    """Test get_mnt with wrong options."""
    with pytest.raises(ValueError, match=r'^min_max_new_tokens must be less than max_max_new_tokens$'):
        tsl.get_mnt(10, {'min_max_new_tokens': 20, 'max_max_new_tokens': 10})


def test_pre_tokenize(string, data_regression):
    """Test tsl module."""
    options = [
        {},
        {'break_newlines': False},
        {'break_chars': '?.!'},
        {'ignore_chars': '?.!'},
        {'break_newlines': False, 'break_chars': '?.!'},
        {'break_newlines': False, 'ignore_chars': '?.!'},
    ]

    res = []
    for option in options:
        dct = {
            'string': string,
            'options': option,
            'tokens': tsl.pre_tokenize(string, **option)
        }
        res.append(dct)

    data_regression.check({'res': res})

def test_load_tsl_model_already_loaded(monkeypatch, mock_called):
    """Test load box model. With already loaded model."""
    model_id = 'test/id'
    monkeypatch.setattr(tsl, 'load_hugginface_model', mock_called)
    monkeypatch.setattr(tsl, 'TSL_MODEL_ID', model_id)
    tsl.load_tsl_model(model_id)

    assert not hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_load_tsl_model_test(monkeypatch):
    """Test load box model. Success"""
    model_id = 'test/id'
    res = {
        'seq2seq': 'mocked_seq2seq',
        'tokenizer': 'mocked_tokenizer',
    }
    monkeypatch.setattr(tsl, 'load_hugginface_model', lambda *args, **kwargs: res)

    # Needed to make sure that changes doen by `load_tsl_model` are not persisted
    for key in tsl_globals:
        monkeypatch.setattr(tsl, key, None)

    assert m.TSLModel.objects.count() == 0
    tsl.load_tsl_model(model_id)
    assert m.TSLModel.objects.count() == 1

    assert tsl.TSL_MODEL_ID == model_id
    # Check that the mocked function was called and that globals were set by loader
    assert tsl.TSL_MODEL == 'mocked_seq2seq'
    assert tsl.TSL_TOKENIZER == 'mocked_tokenizer'

def test_unload_tsl_model(monkeypatch):
    """Test unload box model."""
    for key in tsl_globals:
        monkeypatch.setattr(tsl, key, f'mocked_{key}')

    tsl.unload_tsl_model()

    for key in tsl_globals:
        assert getattr(tsl, key) is None

def test_unload_tsl_model_cpu(monkeypatch, mock_called):
    """Test unload box model with cpu."""
    monkeypatch.setattr(tsl.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(tsl, 'dev', 'cpu')

    tsl.unload_tsl_model()
    assert not hasattr(mock_called, 'called')

def test_unload_tsl_model_cuda(monkeypatch, mock_called):
    """Test unload box model with cuda."""
    monkeypatch.setattr(tsl.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(tsl, 'dev', 'cuda')

    tsl.unload_tsl_model()
    assert hasattr(mock_called, 'called')

def test_get_tsl_model(monkeypatch):
    """Test get ocr model function."""
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', 'test')
    assert tsl.get_tsl_model() == 'test'

def test_pipeline_wrong_type(monkeypatch, mock_tsl_tokenizer):
    """Test tsl pipeline with wrong type."""
    monkeypatch.setattr(tsl, 'TSL_TOKENIZER', mock_tsl_tokenizer('test/id'))
    with pytest.raises(TypeError, match=r'^Unsupported type for text:.*'):
        tsl._tsl_pipeline(1, 'ja', 'en') # pylint: disable=protected-access

def test_pipeline_no_tokens(monkeypatch, mock_tsl_tokenizer):
    """Test tsl pipeline with no tokens generated from pre_tokenize."""
    monkeypatch.setattr(tsl, 'pre_tokenize', lambda *args, **kwargs: [])
    monkeypatch.setattr(tsl, 'TSL_TOKENIZER', mock_tsl_tokenizer('test/id'))

    res = tsl._tsl_pipeline('', 'ja', 'en') # pylint: disable=protected-access

    assert res == ''

def test_pipeline_m2m(monkeypatch, mock_tsl_tokenizer, mock_tsl_model):
    """Test tsl pipeline with m2m model."""
    model_id = 'test/id'
    monkeypatch.setattr(tsl, 'M2M100Tokenizer', mock_tsl_tokenizer)
    monkeypatch.setattr(tsl, 'TSL_MODEL', mock_tsl_model(model_id))
    monkeypatch.setattr(tsl, 'TSL_TOKENIZER', mock_tsl_tokenizer(model_id))

    tsl._tsl_pipeline('', 'ja', 'en') # pylint: disable=protected-access

    assert tsl.TSL_TOKENIZER.called_get_lang_id is True


def test_pipeline(string, monkeypatch, mock_tsl_tokenizer, mock_tsl_model):
    """Test tsl pipeline."""
    model_id = 'test_model'
    lang_src = 'ja'
    lang_dst = 'en'

    monkeypatch.setattr(tsl, 'TSL_MODEL', mock_tsl_model(model_id))
    monkeypatch.setattr(tsl, 'TSL_TOKENIZER', mock_tsl_tokenizer(model_id))

    res = tsl._tsl_pipeline(string, lang_src, lang_dst) # pylint: disable=protected-access

    assert res == string.replace('\n', ' ')
    assert tsl.TSL_TOKENIZER.model_id == model_id
    assert tsl.TSL_TOKENIZER.src_lang == lang_src

def test_pipeline_batch(batch_string, monkeypatch, mock_tsl_tokenizer, mock_tsl_model):
    """Test tsl pipeline with batched string."""
    model_id = 'test_model'
    lang_src = 'ja'
    lang_dst = 'en'

    monkeypatch.setattr(tsl, 'TSL_MODEL', mock_tsl_model(model_id))
    monkeypatch.setattr(tsl, 'TSL_TOKENIZER', mock_tsl_tokenizer(model_id))

    res = tsl._tsl_pipeline(batch_string, lang_src, lang_dst) # pylint: disable=protected-access

    assert res == [_.replace('\n', ' ') for _ in batch_string]
    assert tsl.TSL_TOKENIZER.model_id == model_id
    assert tsl.TSL_TOKENIZER.src_lang == lang_src

@pytest.mark.parametrize(
    'options',
    [
        {},
        {'min_max_new_tokens': 30},
        {'max_max_new_tokens': 22},
        {'max_new_tokens': 15},
        {'max_new_tokens_ratio': 2}
    ],
    ids=[
        'default',
        'min_max_new_tokens',
        'max_max_new_tokens',
        'max_new_tokens',
        'max_new_tokens_ratio'
    ]
)
def test_pipeline_options(options, string, monkeypatch, mock_tsl_tokenizer, mock_tsl_model):
    """Test tsl pipeline with options."""
    model_id = 'test_model'
    lang_src = 'ja'
    lang_dst = 'en'

    monkeypatch.setattr(tsl, 'TSL_MODEL', mock_tsl_model(model_id))
    monkeypatch.setattr(tsl, 'TSL_TOKENIZER', mock_tsl_tokenizer(model_id))

    min_max_new_tokens = options.get('min_max_new_tokens', 20)
    max_max_new_tokens = options.get('max_max_new_tokens', 512)
    ntok = string.replace('\n', ' ').count(' ') + 1

    if min_max_new_tokens > max_max_new_tokens:
        with pytest.raises(ValueError):
            tsl._tsl_pipeline(string, lang_src, lang_dst, options=options) # pylint: disable=protected-access
    else:
        tsl._tsl_pipeline(string, lang_src, lang_dst, options=options) # pylint: disable=protected-access

    mnt = tsl.get_mnt(ntok, options)

    model = tsl.TSL_MODEL

    assert model.options['max_new_tokens'] == mnt

def test_queue_placer_handler(monkeypatch, mock_called):
    """Test queue_placer is setting _tsl_pipeline as handler, and that it is called."""
    monkeypatch.setattr(tsl, '_tsl_pipeline', mock_called)
    monkeypatch.setattr(tsl.q.msg_queue, 'reuse_msg', False)
    tsl.tsl_pipeline(id_=1, block=True)
    assert hasattr(mock_called, 'called')

@pytest.mark.parametrize('mock_called', ['test_return'], indirect=True)
def test_queue_placer_blocking(monkeypatch, mock_called):
    """Test queue_placer with blocking"""
    monkeypatch.setattr(tsl, '_tsl_pipeline', mock_called)
    monkeypatch.setattr(tsl.q.msg_queue, 'reuse_msg', False)
    res = tsl.tsl_pipeline(id_=1, block=True)
    assert hasattr(mock_called, 'called')
    assert res == mock_called.expected

@pytest.mark.parametrize('mock_called', ['test_return'], indirect=True)
def test_queue_placer_nonblocking(monkeypatch, mock_called):
    """Test queue_placer with blocking"""
    monkeypatch.setattr(tsl, '_tsl_pipeline', mock_called)
    monkeypatch.setattr(tsl.q.msg_queue, 'reuse_msg', False)
    tsl.q.stop_workers()
    res = tsl.tsl_pipeline(id_=1, block=False)
    assert isinstance(res, Message)

    assert not hasattr(mock_called, 'called') # Before resolving the message the handler is not called
    tsl.q.start_workers()
    assert res.response() == mock_called.expected
    assert hasattr(mock_called, 'called') # After resolving the message the handler is called


def test_pipeline_worker():
    """Test tsl pipeline with worker"""
    placeholder = 'placeholder'
    tsl.q.stop_workers()

    messages = [tsl.tsl_pipeline(placeholder, 'ja', 'en', id_=i, batch_id=0, block=False) for i in range(3)]
    assert all(isinstance(_, Message) for _ in messages)
    # Makes sure that batching is enabled for tsl queue (retrieve all messages withone `get` call)
    res = tsl.q.get()
    assert len(res) == len(messages)
