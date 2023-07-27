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
"""Tests for ocr module."""

import pytest

from ocr_translate import models as m
from ocr_translate.messaging import Message
from ocr_translate.ocr_tsl import ocr

ocr_globals = ['OCR_MODEL', 'OCR_TOKENIZER', 'OCR_IMAGE_PROCESSOR', 'OCR_MODEL_OBJ', 'OBJ_MODEL_ID']

def test_load_ocr_model_already_loaded(monkeypatch, mock_called):
    """Test load box model. With already loaded model."""
    model_id = 'test/id'
    monkeypatch.setattr(ocr, 'load_hugginface_model', mock_called)
    monkeypatch.setattr(ocr, 'OBJ_MODEL_ID', model_id)
    ocr.load_ocr_model(model_id)

    assert not hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_load_ocr_model_tesseract(monkeypatch, mock_called):
    """Test load box model. Success"""
    model_id = 'tesseract'

    monkeypatch.setattr(ocr, 'load_hugginface_model', mock_called)
    # Needed to make sure that changes doen by `load_ocr_model` are not persisted
    for key in ocr_globals:
        monkeypatch.setattr(ocr, key, None)

    ocr.load_ocr_model(model_id)
    assert not hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_load_ocr_model_test(monkeypatch):
    """Test load box model. Success"""
    model_id = 'easyocr'
    res = {
        'ved_model': 'mocked_ved',
        'tokenizer': 'mocked_tokenizer',
        'image_processor': 'mocked_image_processor',
    }
    monkeypatch.setattr(ocr, 'load_hugginface_model', lambda *args, **kwargs: res)

    # Needed to make sure that changes doen by `load_ocr_model` are not persisted
    for key in ocr_globals:
        monkeypatch.setattr(ocr, key, None)

    assert m.OCRModel.objects.count() == 0
    ocr.load_ocr_model(model_id)
    assert m.OCRModel.objects.count() == 1

    assert ocr.OBJ_MODEL_ID == model_id
    # Check that the mocked function was called and that globals were set by loader
    assert ocr.OCR_MODEL == 'mocked_ved'
    assert ocr.OCR_TOKENIZER == 'mocked_tokenizer'
    assert ocr.OCR_IMAGE_PROCESSOR == 'mocked_image_processor'

def test_unload_ocr_model(monkeypatch):
    """Test unload box model."""
    for key in ocr_globals:
        monkeypatch.setattr(ocr, key, f'mocked_{key}')

    ocr.unload_ocr_model()

    for key in ocr_globals:
        assert getattr(ocr, key) is None

def test_unload_ocr_model_cpu(monkeypatch, mock_called):
    """Test unload box model with cpu."""
    monkeypatch.setattr(ocr.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(ocr, 'dev', 'cpu')

    ocr.unload_ocr_model()
    assert not hasattr(mock_called, 'called')

def test_unload_ocr_model_cuda(monkeypatch, mock_called):
    """Test unload box model with cuda."""
    monkeypatch.setattr(ocr.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(ocr, 'dev', 'cuda')

    ocr.unload_ocr_model()
    assert hasattr(mock_called, 'called')

def test_get_ocr_model(monkeypatch):
    """Test get ocr model function."""
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', 'test')
    assert ocr.get_ocr_model() == 'test'

def test_pipeline_invalide_image():
    """Test ocr pipeline with invalid image."""
    with pytest.raises(TypeError, match=r'^img should be PIL Image.*'):
        ocr._ocr('invalid_image', 'ja') # pylint: disable=protected-access

def test_pipeline_with_bbox(monkeypatch, mock_called, image_pillow):
    """Test ocr pipeline with bbox. Has to call the crop method of image."""
    model_id = 'tesseract'
    bbox = (1,2,8,9)
    monkeypatch.setattr(ocr, 'OBJ_MODEL_ID', model_id)
    monkeypatch.setattr(ocr, 'tesseract_pipeline', lambda *args, **kwargs: None)
    monkeypatch.setattr(ocr.Image.Image, 'crop', mock_called)

    ocr._ocr(image_pillow, '', bbox=bbox) # pylint: disable=protected-access

    assert hasattr(mock_called, 'called')
    assert mock_called.args[1] == bbox # 0 is self

def test_pipeline_tesseract(monkeypatch, mock_called, image_pillow):
    """Test ocr pipeline with tesseract model."""
    model_id = 'tesseract'
    monkeypatch.setattr(ocr, 'OBJ_MODEL_ID', model_id)
    monkeypatch.setattr(ocr, 'tesseract_pipeline', mock_called)

    ocr._ocr(image_pillow, '') # pylint: disable=protected-access

    assert hasattr(mock_called, 'called')

def test_pipeline_hugginface(image_pillow, mock_ocr_preprocessor, mock_ocr_tokenizer, mock_ocr_model, monkeypatch):
    """Test ocr pipeline with hugginface model."""
    model_id = 'test_model'
    lang = 'ja'

    monkeypatch.setattr(ocr, 'OCR_IMAGE_PROCESSOR', mock_ocr_preprocessor(model_id))
    monkeypatch.setattr(ocr, 'OCR_TOKENIZER', mock_ocr_tokenizer(model_id))
    monkeypatch.setattr(ocr, 'OCR_MODEL', mock_ocr_model(model_id))

    res = ocr._ocr(image_pillow, lang) # pylint: disable=protected-access

    assert res == 'abcde'

def test_pipeline_hugginface_cuda(image_pillow, mock_ocr_preprocessor, mock_ocr_tokenizer, mock_ocr_model, monkeypatch):
    """Test ocr pipeline with hugginface model and cuda."""
    model_id = 'test_model'
    lang = 'ja'

    monkeypatch.setattr(ocr, 'dev', 'cuda')
    monkeypatch.setattr(ocr, 'OCR_IMAGE_PROCESSOR', mock_ocr_preprocessor(model_id))
    monkeypatch.setattr(ocr, 'OCR_TOKENIZER', mock_ocr_tokenizer(model_id))
    monkeypatch.setattr(ocr, 'OCR_MODEL', mock_ocr_model(model_id))

    res = ocr._ocr(image_pillow, lang) # pylint: disable=protected-access

    assert res == 'abcde'

def test_queue_placer_handler(monkeypatch, mock_called):
    """Test queue_placer is setting _ocr as handler, and that it is called."""
    monkeypatch.setattr(ocr, '_ocr', mock_called)
    monkeypatch.setattr(ocr.q.msg_queue, 'reuse_msg', False)
    ocr.ocr(id_=1, block=True)
    assert hasattr(mock_called, 'called')

@pytest.mark.parametrize('mock_called', ['test_return'], indirect=True)
def test_queue_placer_blocking(monkeypatch, mock_called):
    """Test queue_placer with blocking"""
    monkeypatch.setattr(ocr, '_ocr', mock_called)
    monkeypatch.setattr(ocr.q.msg_queue, 'reuse_msg', False)
    res = ocr.ocr(id_=1, block=True)
    assert hasattr(mock_called, 'called')
    assert res == mock_called.expected

@pytest.mark.parametrize('mock_called', ['test_return'], indirect=True)
def test_queue_placer_nonblocking(monkeypatch, mock_called):
    """Test queue_placer with blocking"""
    monkeypatch.setattr(ocr, '_ocr', mock_called)
    monkeypatch.setattr(ocr.q.msg_queue, 'reuse_msg', False)
    ocr.q.stop_workers()
    res = ocr.ocr(id_=1, block=False)
    assert isinstance(res, Message)

    assert not hasattr(mock_called, 'called') # Before resolving the message the handler is not called
    ocr.q.start_workers()
    assert res.response() == mock_called.expected
    assert hasattr(mock_called, 'called') # After resolving the message the handler is called

def test_pipeline_worker():
    """Test tsl pipeline with worker"""
    placeholder = 'placeholder'
    ocr.q.stop_workers()

    messages = [ocr.ocr(placeholder, 'ja', 'en', id_=i, block=False) for i in range(3)]
    assert all(isinstance(_, Message) for _ in messages)
    def gen():
        while not ocr.q.msg_queue.empty():
            yield ocr.q.msg_queue.get()
    res = list(gen())
    assert len(res) == len(messages)
