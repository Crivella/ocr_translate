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
"""Tests for easyocr plugin."""

import easyocr
import pytest

from ocr_translate import models as m
from ocr_translate.plugins import easyocr

boxes = [
    ((10,10,30,30), (15,15,20,20)), # b2 inside b1
    ((15,15,20,20), (10,10,30,30)), # b1 inside b2

    ((30,30,50,50), (10,10,20,35)), # l1 > r2
    ((30,30,50,50), (55,10,75,35)), # r1 < l2
    ((30,30,50,50), (10,10,35,20)), # b1 > t2
    ((30,30,50,50), (10,55,35,75)), # t1 < b2

    ((30,30,50,50), (10,10,35,35)), # b2-tr inside b1
    ((30,30,50,50), (45,10,75,35)), # b2-tl inside b1
    ((30,30,50,50), (40,45,75,75)), # b2-bl inside b1
    ((30,30,50,50), (10,45,35,75)), # b2-br inside b1

    ((10,50,70,60), (50,10,60,70)), # intersection, but cornder not inside

    ((10,10,30,30), (29,29,51,40), (50,10,60,30)), # 3x intersection
    ((10,10,30,30), (29,29,51,40), (60,10,70,30)), # 2x intersection + 1
]
ids = [
        'b2_inside_b1',
        'b1_inside_b2',
        'l1_>_r2',
        'r1_<_l2',
        'b1_>_t2',
        't1_<_b2',
        'b2-tr_inside_b1',
        'b2-tl_inside_b1',
        'b2-bl_inside_b1',
        'b2-br_inside_b1',
        'int_nocorners',
        '3x_intersection',
        '2x_intersection_+_1',
]

pytestmark = pytest.mark.django_db

@pytest.fixture()
def easyocr_model(language):
    """OCRBoxModel database object."""
    easyocr_model_dict = {
        'name': 'easyocr',
        'language_format': 'iso1',
        'entrypoint': 'easyocr.box'
    }
    entrypoint = easyocr_model_dict.pop('entrypoint')
    res = m.OCRBoxModel.objects.create(**easyocr_model_dict)
    res.entrypoint = entrypoint
    res.languages.add(language)
    res.save()

    return easyocr.EasyOCRBoxModel.objects.get(name = res.name)

def test_intersection_merge(data_regression):
    """Test intersections function."""

    res = []
    for boxes_lbrt,idx in zip(boxes,ids):
        ptr = {}
        ptr['idx'] = idx
        boxes_lrbt = []
        for l,b,r,t in boxes_lbrt:
            boxes_lrbt.append((l,r,b,t))
        ptr['box_lst'] = boxes_lrbt
        ptr['intersection'] = easyocr.EasyOCRBoxModel.intersections(boxes_lrbt)
        merge = easyocr.EasyOCRBoxModel.merge_bboxes(boxes_lrbt)
        merge = [[int(_) for _ in el] for el in merge]
        ptr['merge'] = merge
        res.append(ptr)

    data_regression.check({'res': res})

def test_load_box_model_easyocr(monkeypatch, easyocr_model: m.OCRBoxModel):
    """Test load box model. Success"""
    monkeypatch.setattr(easyocr.easyocr, 'Reader', lambda *args, **kwargs: 'mocked')
    easyocr_model.load()
    assert easyocr_model.reader == 'mocked'

def test_unload_box_model_easyocr_cpu(monkeypatch, mock_called, easyocr_model: m.OCRBoxModel):
    """Test unload box model with cpu."""
    easyocr_model.dev = 'cpu'
    monkeypatch.setattr(easyocr.torch.cuda, 'empty_cache', mock_called)

    easyocr_model.unload()
    assert not hasattr(mock_called, 'called')

def test_unload_box_model_easyocr_gpu(monkeypatch, mock_called, easyocr_model: m.OCRBoxModel):
    """Test unload box model with cpu."""
    easyocr_model.dev = 'cuda'
    monkeypatch.setattr(easyocr.torch.cuda, 'empty_cache', mock_called)

    easyocr_model.unload()
    assert hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_easyocr_box_detextion(monkeypatch, mock_called, image_pillow, easyocr_model):
    """Test easyocr box detection."""
    class MockReader(): # pylint: disable=missing-class-docstring
        def __init__(self):
            self.called = False
            self.res = None
        def detect(self, *args, **kwargs): # pylint: disable=missing-function-docstring
            self.called = True
            self.res = (('TARGET', 'other1'), 'other2')
            return self.res

    reader = MockReader()
    easyocr_model.reader = reader

    monkeypatch.setattr(easyocr_model, 'merge_bboxes', mock_called)

    easyocr_model._box_detection(image_pillow) # pylint: disable=protected-access

    assert reader.called

    assert hasattr(mock_called, 'called')
    assert mock_called.args[0] == 'TARGET'
