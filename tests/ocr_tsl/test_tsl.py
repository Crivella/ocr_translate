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

from ocr_translate.messaging import Message
from ocr_translate.ocr_tsl import tsl


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


def test_pipeline_worker():
    """Test tsl pipeline with worker"""
    placeholder = 'placeholder'
    tsl.q.stop_workers()

    messages = [tsl.tsl_pipeline(placeholder, 'ja', 'en', id_=i, batch_id=0, block=False) for i in range(3)]
    assert all(isinstance(_, Message) for _ in messages)
    # Makes sure that batching is enabled for tsl queue (retrieve all messages withone `get` call)
    res = tsl.q.get()
    assert len(res) == len(messages)
