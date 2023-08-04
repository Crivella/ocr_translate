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
"""Tests for box module."""

import pytest

from ocr_translate import models as m
# from ocr_translate.messaging import Message
from ocr_translate.ocr_tsl import box

# def test_load_box_model_notimplemented():
#     """Test load box model. With not implemented model."""
#     model_id = 'notimplemented'
#     with pytest.raises(NotImplementedError):
#         box.load_box_model(model_id)

@pytest.mark.django_db
def test_load_box_model(monkeypatch, mock_called, box_model: m.OCRBoxModel):
    """Test load box model from scratch."""
    model_id = box_model.id
    def mock_fromentrypoint(*args, **kwargs):
        mock_fromentrypoint.called = True
        return box_model
    monkeypatch.setattr(m.OCRBoxModel, 'from_entrypoint', mock_fromentrypoint)
    box_model.load = mock_called
    box.load_box_model(model_id)

    assert hasattr(mock_fromentrypoint, 'called')
    assert hasattr(mock_called, 'called')

def test_load_box_model_already_loaded(monkeypatch, mock_called):
    """Test load box model. With already loaded model."""
    model_id = 'easyocr'
    monkeypatch.setattr(m.OCRBoxModel, 'from_entrypoint', mock_called)
    monkeypatch.setattr(box, 'BOX_MODEL_ID', model_id)
    box.load_box_model(model_id)

    assert not hasattr(mock_called, 'called')

def test_get_box_model(monkeypatch):
    """Test get box model function."""
    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', 'test')
    assert box.get_box_model() == 'test'


# def test_queue_placer_handler(monkeypatch, mock_called):
#     """Test queue_placer is setting _box_pipeline as handler, and that it is called."""
#     monkeypatch.setattr(box, '_box_pipeline', mock_called)
#     monkeypatch.setattr(box.q.msg_queue, 'reuse_msg', False)
#     box.box_pipeline(id_=1, block=True)
#     assert hasattr(mock_called, 'called')

# @pytest.mark.parametrize('mock_called', ['test_return'], indirect=True)
# def test_queue_placer_blocking(monkeypatch, mock_called):
#     """Test queue_placer with blocking"""
#     monkeypatch.setattr(box, '_box_pipeline', mock_called)
#     monkeypatch.setattr(box.q.msg_queue, 'reuse_msg', False)
#     res = box.box_pipeline(id_=1, block=True)
#     assert hasattr(mock_called, 'called')
#     assert res == mock_called.expected

# @pytest.mark.parametrize('mock_called', ['test_return'], indirect=True)
# def test_queue_placer_nonblocking(monkeypatch, mock_called):
#     """Test queue_placer with blocking"""
#     monkeypatch.setattr(box, '_box_pipeline', mock_called)
#     monkeypatch.setattr(box.q.msg_queue, 'reuse_msg', False)
#     box.q.stop_workers()
#     res = box.box_pipeline(id_=1, block=False)
#     assert isinstance(res, Message)

#     assert not hasattr(mock_called, 'called') # Before resolving the message the handler is not called
#     box.q.start_workers()
#     assert res.response() == mock_called.expected
#     assert hasattr(mock_called, 'called') # After resolving the message the handler is called

# def test_box_pipeline_worker():
#     """Test tsl pipeline with worker"""
#     placeholder = 'placeholder'
#     box.q.stop_workers()

#     messages = [box.box_pipeline(placeholder, id_=i, block=False) for i in range(3)]
#     assert all(isinstance(_, Message) for _ in messages)
#     def gen():
#         while not box.q.msg_queue.empty():
#             yield box.q.msg_queue.get()
#     res = list(gen())
#     assert len(res) == len(messages)
