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
"""Tests for base plugin facility."""

import pytest

from ocr_translate import models as m
from ocr_translate.ocr_tsl import signals

pytestmark = pytest.mark.django_db

def test_base_from_entrypoint():
    """Test from_entrypoint method of BaseModel should `raise ValueError`."""
    with pytest.raises(ValueError):
        m.BaseModel.from_entrypoint('test_model_id')

def test_box_model_from_entrypoint_unknown(box_model: m.OCRBoxModel):
    """Test from_entrypoint method of OCRModel should `raise ValueError` if entrypoint is unknown."""
    with pytest.raises(ValueError, match=r'^Missing plugin: Entrypoint "test_entrypoint.box" not found.$'):
        m.OCRBoxModel.from_entrypoint(box_model.name)

def test_ocr_model_from_entrypoint_unknown(ocr_model: m.OCRModel):
    """Test from_entrypoint method of OCRModel should `raise ValueError` if entrypoint is unknown."""
    with pytest.raises(ValueError, match=r'^Missing plugin: Entrypoint "test_entrypoint.ocr" not found.$'):
        m.OCRModel.from_entrypoint(ocr_model.name)

def test_tsl_model_from_entrypoint_unknown(tsl_model: m.TSLModel):
    """Test from_entrypoint method of OCRModel should `raise ValueError` if entrypoint is unknown."""
    with pytest.raises(ValueError, match=r'^Missing plugin: Entrypoint "test_entrypoint.tsl" not found.$'):
        m.TSLModel.from_entrypoint(tsl_model.name)

def test_valid_entrypoint(monkeypatch, box_model: m.OCRBoxModel):
    """Test that valid entrypoint works."""
    monkeypatch.setattr(
        m.base, 'entry_points',
        lambda *args, **kwargs: [o,],
        )

    class Obj(): # pylint: disable=missing-class-docstring
        def __init__(self):
            self.called = False
            self.called_name = None

        @property
        def objects(self): # pylint: disable=missing-function-docstring
            class A(): # pylint: disable=missing-class-docstring,invalid-name
                pass
            new = A()
            new.get = self.get # pylint: disable=attribute-defined-outside-init
            return new

        def get(self, name): # pylint: disable=missing-function-docstring
            self.called = True
            self.called_name = name
            return name

        def load(self): # pylint: disable=missing-function-docstring
            return self

    o = Obj() # pylint: disable=invalid-name

    m.OCRBoxModel.from_entrypoint(box_model.name)

    assert o.called
    assert o.called_name == box_model.name

def test_box_load_not_implemented(box_model: m.OCRBoxModel):
    """Test that load method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        box_model.load()

def test_box_unload_not_implemented(box_model: m.OCRBoxModel):
    """Test that unload method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        box_model.unload()

def test_ocr_non_pil_image(ocr_model: m.OCRModel):
    """Test that ocr method raises TypeError if image is not PIL.Image."""
    with pytest.raises(TypeError, match=r'^img should be PIL Image, but got <class \'str\'>$'):
        ocr_model.prepare_image('test_image')

def test_box_main_method_notimplemented(box_model: m.OCRBoxModel):
    """Test that ocr method raises TypeError if image is not PIL.Image."""
    with pytest.raises(NotImplementedError):
        box_model._box_detection('test_image') # pylint: disable=protected-access

def test_ocr_main_method_notimplemented(ocr_model: m.OCRModel):
    """Test that ocr method raises TypeError if image is not PIL.Image."""
    with pytest.raises(NotImplementedError):
        ocr_model._ocr('test_image') # pylint: disable=protected-access

def test_tsl_main_method_notimplemented(tsl_model: m.TSLModel):
    """Test that ocr method raises TypeError if image is not PIL.Image."""
    with pytest.raises(NotImplementedError):
        tsl_model._translate('src_text', 'src_lang', 'dst_lang') # pylint: disable=protected-access

def test_box_get_lang_code(language, box_model: m.OCRBoxModel):
    """Test that get_lang_code uses iso1_map value available."""
    res = box_model.get_lang_code(language)
    assert res == 'jap'

def test_box_get_lang_code_noisomap(language2, box_model: m.OCRBoxModel):
    """Test that get_lang_code uses iso1_map value not available."""
    res = box_model.get_lang_code(language2)
    assert res == 'ja2'

def test_lang_from_dct_new(language_dict):
    """Test creating a new language"""
    assert m.Language.objects.count() == 0
    obj = m.Language.from_dct(language_dict)
    assert m.Language.objects.count() == 1
    assert obj.iso1 == language_dict['iso1']

def test_lang_from_dct_missing_req(language_dict):
    """Test creating a new language"""
    language_dict.pop('iso1')
    with pytest.raises(ValueError):
        m.Language.from_dct(language_dict)

def test_lang_from_dct_existing(language_dict, language):
    """Test creating a new language"""
    obj = m.Language.from_dct(language_dict)
    assert language == obj

def test_lang_load_model(monkeypatch, language, language2, mock_called):
    """Test loading language"""
    assert m.Language.get_loaded_model_src() is None
    assert m.Language.get_loaded_model_dst() is None

    m.Language.load_model_src(language.iso1)

    assert m.Language.get_loaded_model_src() == language
    assert m.Language.get_loaded_model_dst() is None

    m.Language.load_model_dst(language2.iso1)

    assert m.Language.get_loaded_model_src() == language
    assert m.Language.get_loaded_model_dst() == language2

    # Reloading same model should not refresh the cache
    monkeypatch.setattr(signals.refresh_model_cache_signal, 'send', mock_called)
    m.Language.load_model_src(language.iso1)
    m.Language.load_model_dst(language2.iso1)
    assert not hasattr(mock_called, 'called')

    m.Language.load_model_src(language2.iso1)
    assert hasattr(mock_called, 'called')

def test_lang_unload_model(monkeypatch, lang_src_loaded, lang_dst_loaded2, mock_called):
    """Test unloading language"""
    assert m.Language.get_loaded_model_src() == lang_src_loaded
    assert m.Language.get_loaded_model_dst() == lang_dst_loaded2

    m.Language.unload_model_src()
    assert m.Language.get_loaded_model_src() is None
    assert m.Language.get_loaded_model_dst() == lang_dst_loaded2

    m.Language.unload_model_dst()
    assert m.Language.get_loaded_model_src() is None
    assert m.Language.get_loaded_model_dst() is None

    # Unloading again should not refresh the cache
    monkeypatch.setattr(signals.refresh_model_cache_signal, 'send', mock_called)
    m.Language.unload_model_src()
    m.Language.unload_model_dst()
    assert not hasattr(mock_called, 'called')

    monkeypatch.setattr(signals.refresh_model_cache_signal, 'send', lambda *args, **kwargs: None)
    m.Language.load_model_src(lang_src_loaded.iso1)
    monkeypatch.setattr(signals.refresh_model_cache_signal, 'send', mock_called)
    assert not hasattr(mock_called, 'called')
    m.Language.unload_model_src()
    assert hasattr(mock_called, 'called')

def test_base_from_dct_new(box_model_dict):
    """Test creating a new model"""
    assert m.OCRBoxModel.objects.count() == 0
    obj = m.OCRBoxModel.from_dct(box_model_dict)
    assert m.OCRBoxModel.objects.count() == 1
    assert obj.name == box_model_dict['name']

def test_base_from_dct_new_missing_key(box_model_dict):
    """Test creating a new model missing language key"""
    key = list(m.OCRBoxModel.CREATE_LANG_KEYS.keys())[0]
    box_model_dict.pop(key, '')
    with pytest.raises(KeyError):
        m.OCRBoxModel.from_dct(box_model_dict)

def test_base_from_dct_new_wrong_type(box_model_dict):
    """Test creating a new model with wrong data for languages"""
    key = list(m.OCRBoxModel.CREATE_LANG_KEYS.keys())[0]
    box_model_dict[key] = 12345
    with pytest.raises(TypeError):
        m.OCRBoxModel.from_dct(box_model_dict)

def test_base_from_dct_new_both_code_format(box_model_dict):
    """Test creating a new model missing language key"""
    box_model_dict['lang_code'] = 'abc'
    box_model_dict['language_format'] = 'xyz'
    obj = m.OCRBoxModel.from_dct(box_model_dict)

    assert obj.language_format == 'xyz'

def test_base_from_dct_update(box_model_dict, box_model):
    """Test creating a new model missing language key"""
    assert box_model.language_format == box_model_dict['language_format']
    assert box_model.languages.count() > 0
    box_model_dict['language_format'] = 'xyz'
    box_model_dict['lang'] = []
    m.OCRBoxModel.from_dct(box_model_dict)
    box_model.refresh_from_db()
    assert box_model.language_format == 'xyz'
    assert box_model.languages.count() == 0

def test_base_load_model(monkeypatch, box_model, mock_called):
    """Test load_model method of OCRBoxModel."""
    monkeypatch.setattr(m.OCRBoxModel, 'from_entrypoint', lambda name: box_model)
    monkeypatch.setattr(m.OCRBoxModel, 'load', mock_called)
    assert not hasattr(mock_called, 'called')
    obj1 = m.OCRBoxModel.load_model(box_model.name)
    assert hasattr(mock_called, 'called')
    del mock_called.called

    # Load again should not call `load` again
    obj2 = m.OCRBoxModel.load_model(box_model.name)
    assert not hasattr(mock_called, 'called')
    assert obj1 is obj2

def test_base_unload_model(monkeypatch, box_model_loaded, mock_called):
    """Test unload_model method of OCRBoxModel."""
    monkeypatch.setattr(m.OCRBoxModel, 'unload', mock_called)
    assert not hasattr(mock_called, 'called')
    m.OCRBoxModel.unload_model()
    assert hasattr(mock_called, 'called')
    del mock_called.called

    # Unload again should not call `unload` again
    m.OCRBoxModel.unload_model()
    assert not hasattr(mock_called, 'called')
