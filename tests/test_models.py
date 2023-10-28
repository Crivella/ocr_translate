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
"""Tests for the database models."""
#pylint: disable=protected-access

from dataclasses import dataclass

import django
import numpy as np
import pytest
from PIL.Image import Image as PILImage

from ocr_translate import models as m
from ocr_translate import tries
from ocr_translate.messaging import Message
from ocr_translate.ocr_tsl import box, full, lang, ocr, tsl
from ocr_translate.trie import Trie

pytestmark = pytest.mark.django_db

def test_add_language(language_dict: dict, language: m.Language):
    """Test adding a language."""
    query = m.Language.objects.filter(**language_dict)
    assert query.exists()
    assert str(query.first()) == language_dict['iso1']

def test_add_language_existing(language_dict: dict, language: m.Language):
    """Test adding a language."""
    with pytest.raises(django.db.utils.IntegrityError):
        m.Language.objects.create(**language_dict)

def test_language_eq_obj(language: m.Language):
    """Test language equality."""
    assert language == language # pylint: disable=comparison-with-itself

def test_language_eq_iso1(language: m.Language):
    """Test language equality."""
    assert language == language.iso1

def test_add_ocr_box_model(box_model_dict: dict, box_model: m.OCRBoxModel):
    """Test adding a new OCRBoxModel"""
    query = m.OCRBoxModel.objects.filter(**box_model_dict)
    assert query.exists()
    assert str(query.first()) == box_model_dict['name']

def test_add_ocr_model(ocr_model_dict: dict, ocr_model: m.OCRModel):
    """Test adding a new OCRModel"""
    query = m.OCRModel.objects.filter(**ocr_model_dict)
    assert query.exists()
    assert str(query.first()) == ocr_model_dict['name']

def test_add_tsl_model(tsl_model_dict: dict, tsl_model: m.TSLModel):
    """Test adding a new TSLModel"""
    query = m.TSLModel.objects.filter(**tsl_model_dict)
    assert query.exists()
    assert str(query.first()) == tsl_model_dict['name']

def test_add_option_dict(option_dict: m.OptionDict):
    """Test adding a new OptionDict"""
    query = m.OptionDict.objects.filter(options={})
    assert query.exists()
    assert str(query.first()) == str({})

def test_box_run(
        monkeypatch, image: m.Image, language: m.Language, box_model: m.OCRBoxModel, option_dict: m.OptionDict
        ):
    """Test adding a new BoxRun"""

    lbrt = (1,2,3,4)
    def mock_pipeline(*args, **kwargs):
        return [{'single': [lbrt], 'merged': lbrt}]

    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    box_model._box_detection = mock_pipeline

    single, merged = box_model.box_detection(image, language, image=1, options=option_dict)

    assert isinstance(single, list)
    assert isinstance(merged, list)
    assert isinstance(single[0], m.BBox)
    assert isinstance(merged[0], m.BBox)
    assert merged[0].lbrt == lbrt

def test_box_run_reuse(
        monkeypatch, image: m.Image, language: m.Language, box_model: m.OCRBoxModel, option_dict: m.OptionDict
        ):
    """Test adding a new BoxRun"""
    lbrt = (1,2,3,4)
    def mock_pipeline(*args, **kwargs):
        return [{'single': [lbrt], 'merged': lbrt}]

    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    box_model._box_detection = mock_pipeline

    assert m.OCRBoxRun.objects.count() == 0
    box_model.box_detection(image, language, image=1, options=option_dict)
    assert m.OCRBoxRun.objects.count() == 1
    box_model.box_detection(image, language, image=1, options=option_dict)
    assert m.OCRBoxRun.objects.count() == 1

def test_ocr_run_nooption(
        monkeypatch, image_pillow: PILImage,
        bbox: m.BBox, language: m.Language, ocr_model: m.OCRModel, option_dict: m.OptionDict
        ):
    """Test performing an ocr_run blocking"""
    text = 'test_text'
    def mock_ocr(*args, **kwargs):
        return text

    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    ocr_model._ocr = mock_ocr

    gen = ocr_model.ocr(bbox, language, image=image_pillow)

    res = next(gen)

    assert isinstance(res, m.Text)
    assert res.text == text
    assert res.from_ocr_merged.first().options.options == {}

def test_ocr_run_noimage(
        monkeypatch,
        bbox: m.BBox, language: m.Language, ocr_model: m.OCRModel, option_dict: m.OptionDict
        ):
    """Test performing an ocr_run blocking"""
    text = 'test_text'
    def mock_ocr(*args, **kwargs):
        return text

    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    ocr_model._ocr = mock_ocr

    gen = ocr_model.ocr(bbox, language, options=option_dict)

    with pytest.raises(ValueError, match=r'^Image is required for OCR$'):
        next(gen)

def test_ocr_run(
        monkeypatch, mock_called, image_pillow: PILImage,
        bbox: m.BBox, language: m.Language, ocr_model: m.OCRModel, option_dict: m.OptionDict
        ):
    """Test performing an ocr_run blocking + same pipeline (has to run lazily by refetching previous result)"""
    text = 'test_text'
    def mock_ocr(*args, **kwargs):
        return text

    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    ocr_model._ocr = mock_ocr

    gen = ocr_model.ocr(bbox, language, image=image_pillow, options=option_dict)

    res = next(gen)

    assert isinstance(res, m.Text)
    assert res.text == text

    ocr_model._ocr = mock_called # Should not be called as it should be lazy
    gen_lazy = ocr_model.ocr(bbox, language, image=image_pillow, options=option_dict)

    assert not hasattr(mock_called, 'called')
    assert next(gen_lazy) == res

def test_ocr_run_nonblock(
        monkeypatch, mock_called, image_pillow: PILImage,
        bbox: m.BBox, language: m.Language, ocr_model: m.OCRModel, option_dict: m.OptionDict
        ):
    """Test performing an ocr_run non-blocking + same pipeline (has to run lazily by refetching previous result)"""
    text = 'test_text'
    def mock_ocr(*args, **kwargs):
        return text

    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    ocr_model._ocr = mock_ocr

    gen = ocr_model.ocr(bbox, language, image=image_pillow, options=option_dict, block=False)

    msg = next(gen)
    # msg.resolve()
    res = next(gen)

    assert isinstance(msg, Message)
    assert isinstance(res, m.Text)
    assert res.text == text

    ocr_model._ocr = mock_called # Should not be called as it should be lazy
    gen_lazy = ocr_model.ocr(bbox, language, image=image_pillow, options=option_dict, block=False)

    assert not hasattr(mock_called, 'called')
    assert next(gen_lazy) is None
    assert next(gen_lazy) == res

@pytest.mark.parametrize('lang_src', ['ja', 'en'])
def test_ocr_merge_single_result(lang_src): # pylint: disable=too-many-locals
    # pylint: disable=invalid-name
    """Test merge_single_result behavior"""
    @dataclass
    class BBox:
        """Mock BBox class not related to database"""
        l: int
        b: int
        r: int
        t: int
        to_merged: 'BBox' = None

        def __post_init__(self, *args, **kwargs):
            self.id = np.random.rand(1)[0]

        @property
        def lbrt(self): # pylint: disable=missing-function-docstring
            return self.l, self.b, self.r, self.t

        def __hash__(self):
            return hash(self.id)

    merged_lst = [
        BBox(0, 100, 30, 130),
        BBox(100, 0, 130, 30),
        BBox(50, 50, 80, 80),
    ]

    w = 10
    h = 10
    s = 2
    rrx = 2
    rry = 2
    boxes = []
    np.random.seed(0)
    for merged in merged_lst:
        xoff = merged.l
        yoff = merged.b
        for i in range(9):
            errx =  np.random.rand(2) * rrx
            erry =  np.random.rand(2) * rry
            l = i % 3 * (w+s) + xoff + errx[0]
            b = i // 3 * (w+s) + yoff + errx[1]
            r = l + w + erry[0]
            t = b + h + erry[1]
            boxes.append((str(i+1), BBox(l, b, r, t, merged)))

    texts = [_[0] for _ in boxes]
    bboxes_single = [_[1] for _ in boxes]

    vertical = lang_src in  m.OCRModel._VERTICAL_LANGS
    expected = '369258147' if vertical else '1 2 3 4 5 6 7 8 9'

    res = m.OCRModel.merge_single_result(lang_src, texts, bboxes_single, merged_lst)

    for result in res:
        assert result == expected



def test_tsl_pre_tokenize(data_regression, string: str):
    """Test tsl module."""
    options = [
        {},
        {'break_newlines': True},
        {'break_newlines': False},
        {'break_chars': '?.!'},
        {'ignore_chars': '?.!'},
        {'break_newlines': False, 'break_chars': '?.!'},
        {'break_newlines': False, 'ignore_chars': '?.!'},
        {'restore_dash_newlines': True},
    ]

    res = []
    for option in options:
        dct = {
            'string': string,
            'options': option,
            'tokens': m.TSLModel.pre_tokenize(string, **option)
        }
        res.append(dct)

    data_regression.check({'res': res})

@pytest.mark.parametrize('extra_start', ['$', '$%n', 'n$', 'n$$'])
def test_tsl_pre_tokenize_allowed_start(extra_start):
    """Test pre_tokenize with allowed_start_end."""
    pret = m.TSLModel.pre_tokenize
    res = pret(extra_start + ' ' + 'apple', allowed_start_end='a-zA-Z0-9\\-\\.\\,\\;\\?\\! ')
    assert res[0].strip() == 'apple'

@pytest.mark.parametrize('extra_end', ['$', '$%n', 'n$', 'n$$'])
def test_tsl_pre_tokenize_allowed_end(extra_end):
    """Test pre_tokenize with allowed_start_end."""
    pret = m.TSLModel.pre_tokenize
    res = pret('apple' + ' ' + extra_end, allowed_start_end='a-zA-Z0-9\\-\\.\\,\\;\\?\\! ')
    assert res[0].strip() == 'apple'

def test_tsl_pre_tokenize_restorespaces(monkeypatch):
    """Test pre_tokenize with restore spaces."""
    trie = Trie()
    trie.insert('app')
    trie.insert('apple')
    trie.insert('pie')
    monkeypatch.setattr(tries, 'TRIE_SRC', trie)
    res = m.TSLModel.pre_tokenize('applepie', restore_missing_spaces=True)
    assert res == ['apple pie']

def test_tsl_run(
        monkeypatch, mock_called,
        text: m.Text, language: m.Language, tsl_model: m.TSLModel, option_dict: m.OptionDict
        ):
    """Test performing an tsl_run blocking"""
    def mock_tsl_pipeline(*args, **kwargs):
        return text.text

    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)
    tsl_model._translate = mock_tsl_pipeline

    gen = tsl_model.translate(text, src=language, dst=language, options=option_dict)

    res = next(gen)

    assert isinstance(res, m.Text)
    assert res.text == text.text

    tsl_model._translate = mock_called # Should not be called as it should be lazy
    gen_lazy = tsl_model.translate(text, src=language, dst=language, options=option_dict)

    assert not hasattr(mock_called, 'called')
    assert next(gen_lazy) == res

def test_tsl_run_nonblock(
        monkeypatch, mock_called,
        text: m.Text, language: m.Language, tsl_model: m.TSLModel, option_dict: m.OptionDict
        ):
    """Test performing an tsl_run non-blocking"""
    def mock_tsl_pipeline(*args, **kwargs):
        return text.text

    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)
    tsl_model._translate = mock_tsl_pipeline

    gen = tsl_model.translate(text, src=language, dst=language, options=option_dict, block=False)

    msg = next(gen)
    # msg.resolve()
    res = next(gen)

    assert isinstance(msg, Message)
    assert isinstance(res, m.Text)
    assert res.text == text.text

    tsl_model._translate = mock_called # Should not be called as it should be lazy
    gen_lazy = tsl_model.translate(text, src=language, dst=language, options=option_dict, block=False)

    assert not hasattr(mock_called, 'called')
    assert next(gen_lazy) is None
    assert next(gen_lazy) == res

def test_tsl_run_lazy(text: m.Text, language: m.Language, tsl_model: m.TSLModel, option_dict: m.OptionDict):
    """Test tsl pipeline with worker"""
    # Force and lazy should not be used together
    with pytest.raises(ValueError):
        gen = tsl_model.translate(text, language, language, force=True, lazy=True)
        next(gen)

    # Nothing in the DB, so should rise ValueError (no previous found and lazy=True)
    with pytest.raises(ValueError):
        gen = tsl_model.translate(text, language, language, lazy=True)
        next(gen)

@pytest.mark.parametrize('mock_called', [['test_text_ocred']], indirect=True)
def test_ocr_tsl_work_single_ocr_plus_lazy( # pylint: disable=too-many-arguments
        monkeypatch, image_pillow: PILImage, mock_called,
        image: m.Image, text: m.Text, bbox: m.BBox, bbox_single: m.BBox, language: m.Language,
        box_model: m.OCRBoxModel, ocr_model_single: m.OCRModel, tsl_model: m.TSLModel, option_dict: m.OptionDict
        ):
    """Test performing an ocr_tsl_run non-lazy"""
    def mock_box_run(*args, **kwargs):
        return [bbox_single], [bbox]
    def mock_ocr_run(*args, block=True, **kwargs):
        if not block:
            yield
        res, _ = m.Text.objects.get_or_create(text = text.text + '_ocred')
        yield res
    def mock_tsl_run(obj, *args, block=True, **kwargs):
        if not block:
            yield
        res, _ = m.Text.objects.get_or_create(text = obj.text + '_translated')
        yield res

    box_model.box_detection = mock_box_run
    ocr_model_single.ocr = mock_ocr_run
    tsl_model.translate = mock_tsl_run

    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(ocr_model_single, 'merge_single_result', mock_called)

    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model_single)
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)

    res = full.ocr_tsl_pipeline_work(image_pillow, image.md5)

    # Check that `merge_single_result` is being called with the expected arguments
    assert mock_called.args[0] == language.iso1
    assert mock_called.args[1] == [text.text + '_ocred']
    assert mock_called.args[2] == [bbox_single]
    assert mock_called.args[3] == [bbox]

    res_lazy = full.ocr_tsl_pipeline_lazy(image.md5)

    assert res == res_lazy

def test_ocr_tsl_work_plus_lazy(
        monkeypatch, image_pillow: PILImage,
        image: m.Image, text: m.Text, bbox: m.BBox, language: m.Language,
        box_model: m.OCRBoxModel, ocr_model: m.OCRModel, tsl_model: m.TSLModel, option_dict: m.OptionDict
        ):
    """Test performing an ocr_tsl_run non-lazy"""
    def mock_box_run(*args, **kwargs):
        return [bbox], [bbox]
    def mock_ocr_run(*args, block=True, **kwargs):
        if not block:
            yield
        res, _ = m.Text.objects.get_or_create(text = text.text + '_ocred')
        yield res
    def mock_tsl_run(obj, *args, block=True, **kwargs):
        if not block:
            yield
        res, _ = m.Text.objects.get_or_create(text = obj.text + '_translated')
        yield res

    box_model.box_detection = mock_box_run
    ocr_model.ocr = mock_ocr_run
    tsl_model.translate = mock_tsl_run

    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)

    res = full.ocr_tsl_pipeline_work(image_pillow, image.md5)

    assert isinstance(res, list)
    assert len(res) == 1
    assert isinstance(res[0], dict)
    assert res[0]['ocr'] == text.text + '_ocred'
    assert res[0]['tsl'] == text.text + '_ocred' + '_translated'
    assert res[0]['box'] == bbox.lbrt

    res_lazy = full.ocr_tsl_pipeline_lazy(image.md5)

    assert res == res_lazy

def test_ocr_tsl_lazy():
    """Test performing an ocr_tsl_run lazy (no image)"""
    with pytest.raises(ValueError, match=r'^Image with md5 .* does not exist$'):
        full.ocr_tsl_pipeline_lazy('')

def test_ocr_tsl_lazy_image(
        monkeypatch, image: m.Image,
        box_model: m.OCRBoxModel, ocr_model: m.OCRModel, tsl_model: m.TSLModel, option_dict: m.OptionDict
        ):
    """Test performing an ocr_tsl_run lazy (with image but missing ocr-tsl steps)"""
    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)

    with pytest.raises(ValueError):
        full.ocr_tsl_pipeline_lazy(image.md5)
