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
"""Test environment initialization."""

# pylint: disable=redefined-outer-name

import pytest
from django.db.utils import OperationalError

from ocr_translate import models as m
from ocr_translate.ocr_tsl import initializers as ini

pytestmark = pytest.mark.django_db

# Tests for run_on_env
def test_run_on_env_unkown(monkeypatch, mock_called):
    """Test call on env variable unkown."""
    out = ''
    def log_warning(msg):
        """Mock log warning."""
        nonlocal out
        out += msg

    monkeypatch.setenv('TEST', 'false')
    monkeypatch.setattr(ini.logger, 'warning', log_warning)

    assert not hasattr(mock_called, 'called')
    ini.run_on_env('TEST', {'true': mock_called})
    assert not hasattr(mock_called, 'called')

    assert 'Unknown value for environment variable' in out

def test_run_on_env_true(monkeypatch, mock_called):
    """Test call on env variable."""
    monkeypatch.setenv('TEST', 'True')

    assert not hasattr(mock_called, 'called')
    ini.run_on_env('TEST', {'true': mock_called})
    assert hasattr(mock_called, 'called')

def test_run_on_env_tuple(monkeypatch, mock_called):
    """Test call on env variable."""
    assert not hasattr(mock_called, 'called')
    monkeypatch.setenv('TEST', 'True')
    ini.run_on_env('TEST', {('true', '1'): mock_called})
    assert hasattr(mock_called, 'called')

    delattr(mock_called, 'called')

    assert not hasattr(mock_called, 'called')
    monkeypatch.setenv('TEST', '1')
    ini.run_on_env('TEST', {('true', '1'): mock_called})
    assert hasattr(mock_called, 'called')

    delattr(mock_called, 'called')

    assert not hasattr(mock_called, 'called')
    monkeypatch.setenv('TEST', 'tr')
    ini.run_on_env('TEST', {('true', '1'): mock_called})
    assert not hasattr(mock_called, 'called')

def test_run_on_env_invalid_key(monkeypatch):
    """Test call on env variable."""
    monkeypatch.setenv('TEST', 'True')
    with pytest.raises(ValueError) as excinfo:
        ini.run_on_env('TEST', {123: lambda: None})
    assert 'Invalid use of `run_on_env`' in str(excinfo.value)

def test_run_on_env_notdef(mock_called):
    """Test call on env variable."""
    assert not hasattr(mock_called, 'called')
    ini.run_on_env('TEST', {'true': mock_called})
    assert not hasattr(mock_called, 'called')

def test_run_on_env_raise(monkeypatch):
    """Test call on env variable."""
    out = ''
    def log_warning(msg):
        """Mock log warning."""
        nonlocal out
        out += msg

    monkeypatch.setenv('TEST', 'True')
    monkeypatch.setattr(ini.logger, 'warning', log_warning)
    def func():
        raise OperationalError('Test')
    ini.run_on_env('TEST', {'true': func})

    assert 'Ignoring environment variable' in out

def test_init_most_used_clean(mock_loaders):
    """Test init_most_used with empty database."""
    ini.init_most_used()
    assert m.OCRBoxModel.LOADED_MODEL is None
    assert m.OCRModel.LOADED_MODEL is None
    assert m.TSLModel.LOADED_MODEL is None
    assert m.Language.LOADED_SRC is None
    assert m.Language.LOADED_DST is None

def test_init_most_used_content_nousage(mock_loaders, language, box_model, ocr_model, tsl_model):
    """Test init_most_used with content in the database."""
    ini.init_most_used()
    assert m.OCRBoxModel.LOADED_MODEL is None
    assert m.OCRModel.LOADED_MODEL is None
    assert m.TSLModel.LOADED_MODEL is None
    assert m.Language.LOADED_SRC is None
    assert m.Language.LOADED_DST is None

def test_init_most_used_content_partial_usage_box(
        mock_loaders, language, box_model, ocr_model, tsl_model, box_run,
        ):
    """Test init_most_used with content in the database."""
    ini.init_most_used()
    assert m.OCRBoxModel.LOADED_MODEL == box_model
    assert m.OCRModel.LOADED_MODEL is None
    assert m.TSLModel.LOADED_MODEL is None
    assert m.Language.LOADED_SRC is None
    assert m.Language.LOADED_DST is None

def test_init_most_used_content_partial_usage_ocr(
        mock_loaders, language, box_model, ocr_model, tsl_model, ocr_run,
        ):
    """Test init_most_used with content in the database."""
    ini.init_most_used()
    assert m.OCRBoxModel.LOADED_MODEL == box_model
    assert m.OCRModel.LOADED_MODEL == ocr_model
    assert m.TSLModel.LOADED_MODEL is None
    assert m.Language.LOADED_SRC is None
    assert m.Language.LOADED_DST is None

def test_init_most_used_content_partial_usage_tsl(
        mock_loaders, language, box_model, ocr_model, tsl_model, tsl_run
        ):
    """Test init_most_used with content in the database."""
    ini.init_most_used()
    assert m.OCRBoxModel.LOADED_MODEL is None
    assert m.OCRModel.LOADED_MODEL is None
    assert m.TSLModel.LOADED_MODEL == tsl_model
    assert m.Language.LOADED_SRC == language
    assert m.Language.LOADED_DST == language

def test_init_most_used_content_full_usage(
        mock_loaders, language, box_model, ocr_model, tsl_model,
        box_run, ocr_run, tsl_run
        ):
    """Test init_most_used with content in the database."""
    ini.init_most_used()
    assert m.OCRBoxModel.LOADED_MODEL == box_model
    assert m.OCRModel.LOADED_MODEL == ocr_model
    assert m.TSLModel.LOADED_MODEL == tsl_model
    assert m.Language.LOADED_SRC == language
    assert m.Language.LOADED_DST == language


def test_init_most_used_more_content(mock_loaders, language_dict, image, option_dict, text):
    """Test init_most_used with more content in the database. Check that sorting is working."""
    # pylint: disable=unused-variable,too-many-locals
    dct1 = {k:v+'1' for k,v in language_dict.items()}
    dct2 = {k:v+'2' for k,v in language_dict.items()}
    dct3 = {k:v+'3' for k,v in language_dict.items()}
    lang1 = m.Language.objects.create(**dct1)
    lang2 = m.Language.objects.create(**dct2)
    lang3 = m.Language.objects.create(**dct3)

    ocr_box_model1 = m.OCRBoxModel.objects.create(name='test_model1/id')
    ocr_box_model2 = m.OCRBoxModel.objects.create(name='test_model2/id')

    ocr_model1 = m.OCRModel.objects.create(name='test_model1/id')
    ocr_model2 = m.OCRModel.objects.create(name='test_model2/id')

    tsl_model1 = m.TSLModel.objects.create(name='test_model1/id')
    tsl_model2 = m.TSLModel.objects.create(name='test_model2/id')

    box_run1 = m.OCRBoxRun.objects.create(
        model=ocr_box_model1, lang_src=lang1, image=image, options=option_dict
        )
    box_run2_1 = m.OCRBoxRun.objects.create(
        model=ocr_box_model2, lang_src=lang2, image=image, options=option_dict
        )
    box_run2_2 = m.OCRBoxRun.objects.create(
        model=ocr_box_model2, lang_src=lang2, image=image, options=option_dict
        )

    bbox = m.BBox.objects.create(image=image, l=1, b=2, r=3, t=4, from_ocr_merged=box_run1)

    ocr_run1 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model1, options=option_dict, result_merged=text
        )
    ocr_run2_1 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model2, options=option_dict, result_merged=text
        )
    ocr_run2_2 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model2, options=option_dict, result_merged=text
        )

    tsl_run1_1 = m.TranslationRun.objects.create(
        lang_src=lang2, lang_dst=lang3, text=text, model=tsl_model1, options=option_dict, result=text
        )
    tsl_run1_2 = m.TranslationRun.objects.create(
        lang_src=lang2, lang_dst=lang3, text=text, model=tsl_model1, options=option_dict, result=text
        )
    tsl_run2 = m.TranslationRun.objects.create(
        lang_src=lang1, lang_dst=lang1, text=text, model=tsl_model2, options=option_dict, result=text
        )

    ini.init_most_used()

    assert m.Language.LOADED_SRC == lang2
    assert m.Language.LOADED_DST == lang3

    assert m.OCRBoxModel.LOADED_MODEL == ocr_box_model2
    assert m.OCRModel.LOADED_MODEL == ocr_model2
    assert m.TSLModel.LOADED_MODEL == tsl_model1

def test_init_last_used_clean(mock_loaders):
    """Test init_last_used with empty database."""
    ini.init_last_used()
    assert m.OCRBoxModel.LOADED_MODEL is None
    assert m.OCRModel.LOADED_MODEL is None
    assert m.TSLModel.LOADED_MODEL is None
    assert m.Language.LOADED_SRC is None
    assert m.Language.LOADED_DST is None

def test_init_last_used_partial(mock_loaders, language, language2):
    """Test init_last_used with content in the database."""
    language.load_src()
    language2.load_dst()
    ini.init_last_used()
    assert m.OCRBoxModel.LOADED_MODEL is None
    assert m.OCRModel.LOADED_MODEL is None
    assert m.TSLModel.LOADED_MODEL is None
    assert m.Language.LOADED_SRC == language
    assert m.Language.LOADED_DST == language2

    language.load_dst()
    language2.load_src()
    ini.init_last_used()
    assert m.OCRBoxModel.LOADED_MODEL is None
    assert m.OCRModel.LOADED_MODEL is None
    assert m.TSLModel.LOADED_MODEL is None
    assert m.Language.LOADED_SRC == language2
    assert m.Language.LOADED_DST == language

def test_init_last_used_full(mock_loaders, monkeypatch, language, language2, ocr_model, box_model, tsl_model):
    """Test init_last_used with content in the database."""
    monkeypatch.setattr(ocr_model, 'load', lambda: None)
    monkeypatch.setattr(box_model, 'load', lambda: None)
    monkeypatch.setattr(tsl_model, 'load', lambda: None)

    language.load_src()
    language2.load_dst()
    ocr_model.load()
    box_model.load()
    tsl_model.load()

    assert m.OCRBoxModel.LOADED_MODEL is None
    assert m.OCRModel.LOADED_MODEL is None
    assert m.TSLModel.LOADED_MODEL is None
    assert m.Language.LOADED_SRC is None
    assert m.Language.LOADED_DST is None

    ini.init_last_used()
    assert m.OCRBoxModel.LOADED_MODEL == box_model
    assert m.OCRModel.LOADED_MODEL == ocr_model
    assert m.TSLModel.LOADED_MODEL == tsl_model
    assert m.Language.LOADED_SRC == language
    assert m.Language.LOADED_DST == language2

def test_auto_create_languages():
    """Test auto_create_languages."""
    ini.auto_create_languages()

    assert m.Language.objects.count() > 50

    # Test settings of **kwargs
    jap = m.Language.objects.get(iso1='ja')
    assert jap.default_options.options['break_chars'] is not None
    assert jap.default_options.options['break_chars'] is not None

def test_load_ept_data(monkeypatch):
    """Test load_ept_data function."""
    def mock_entrypoints(*, group):
        assert group == '123'
        class Ept:
            """Mock entrypoint"""
            def load(self):
                """Mock entrypoint loader"""
                return {'i am': 'an entrypoint'}

        return Ept(), Ept()

    monkeypatch.setattr(ini, 'entry_points', mock_entrypoints)

    ept1, ept2 = ini.load_ept_data('123') # pylint: disable=unbalanced-tuple-unpacking
    assert ept1['i am'] == 'an entrypoint'
    assert ept2['i am'] == 'an entrypoint'
    ept1.pop('i am')

    assert 'i am' not in ept1
    assert 'i am' in ept2

def test_create_models_nolang(monkeypatch, mock_load_ept):
    """Test auto_create_models without creating languages before"""
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept)
    with pytest.raises(ValueError):
        for ocr in ini.load_ept_data('ocr_translate.ocr_data'):
            m.OCRModel.from_dct(ocr)

def test_auto_create_models_test_data(monkeypatch, mock_load_ept):
    """Test creating dummy models"""
    # Needed after no more entrypoint are defined here

    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept)
    ini.auto_create_languages()

    for box in ini.load_ept_data('ocr_translate.box_data'):
        m.OCRBoxModel.from_dct(box)
    for ocr in ini.load_ept_data('ocr_translate.ocr_data'):
        m.OCRModel.from_dct(ocr)
    for tsl in ini.load_ept_data('ocr_translate.tsl_data'):
        m.TSLModel.from_dct(tsl)

    assert m.OCRBoxModel.objects.count() > 0
    assert m.OCRModel.objects.count() > 0
    assert m.TSLModel.objects.count() > 0

@pytest.mark.django_db
def test_create_new_model_box(monkeypatch, box_model_dict):
    """Test creating a new box model with sync function."""
    def mock_load_ept_data(namespace):
        if namespace.endswith('.box_data'):
            return [box_model_dict]
        return []
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept_data)
    assert m.OCRBoxModel.objects.count() == 0
    assert m.OCRModel.objects.count() == 0
    assert m.TSLModel.objects.count() == 0
    ini.sync_models_epts()
    assert m.OCRBoxModel.objects.count() == 1
    assert m.OCRModel.objects.count() == 0
    assert m.TSLModel.objects.count() == 0

@pytest.mark.django_db
def test_create_new_model_ocr(monkeypatch, ocr_model_dict):
    """Test creating a new ocr model with sync function."""
    def mock_load_ept_data(namespace):
        if namespace.endswith('.ocr_data'):
            return [ocr_model_dict]
        return []
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept_data)
    assert m.OCRBoxModel.objects.count() == 0
    assert m.OCRModel.objects.count() == 0
    assert m.TSLModel.objects.count() == 0
    ini.sync_models_epts()
    assert m.OCRBoxModel.objects.count() == 0
    assert m.OCRModel.objects.count() == 1
    assert m.TSLModel.objects.count() == 0

@pytest.mark.django_db
def test_create_new_model_tsl(monkeypatch, tsl_model_dict):
    """Test creating a new tsl model with sync function."""
    def mock_load_ept_data(namespace):
        if namespace.endswith('.tsl_data'):
            return [tsl_model_dict]
        return []
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept_data)
    assert m.OCRBoxModel.objects.count() == 0
    assert m.OCRModel.objects.count() == 0
    assert m.TSLModel.objects.count() == 0
    ini.sync_models_epts()
    assert m.OCRBoxModel.objects.count() == 0
    assert m.OCRModel.objects.count() == 0
    assert m.TSLModel.objects.count() == 1

@pytest.mark.django_db
def test_sync_update(monkeypatch, box_model_dict, box_model, mock_called):
    """Test sync update existing model."""
    def mock_load_ept_data(namespace):
        if namespace.endswith('.box_data'):
            return [box_model_dict]
        return []
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept_data)
    monkeypatch.setattr(m.OCRBoxModel, 'from_dct', mock_called)
    assert not hasattr(mock_called, 'called')
    ini.sync_models_epts()
    assert hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_sync_create_missing(monkeypatch, box_model_dict, box_model, ocr_model_dict, mock_called):
    """Test sync create missing model."""
    def mock_load_ept_data(namespace):
        if namespace.endswith('.box_data'):
            return [box_model_dict]
        if namespace.endswith('.ocr_data'):
            return [ocr_model_dict]
        return []
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept_data)
    monkeypatch.setattr(m.OCRModel, 'from_dct', mock_called)
    assert not hasattr(mock_called, 'called')
    ini.sync_models_epts()
    assert hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_activate_models(monkeypatch, box_model_dict, box_model):
    """Test initializer deactivate missing models."""
    def mock_load_ept_data(namespace):  # pylint: disable=unused-argument
        if namespace.endswith('.box_data'):
            return [box_model_dict]
        return []
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept_data)
    assert box_model.active
    box_model.deactivate()
    assert not box_model.active
    ini.sync_models_epts()
    box_model.refresh_from_db()
    assert box_model.active

@pytest.mark.django_db
def test_deactivate_missing_models(monkeypatch,box_model, ocr_model, tsl_model):
    """Test initializer deactivate missing models."""
    def mock_load_ept_data(namespace):  # pylint: disable=unused-argument
        return []
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept_data)
    assert box_model.active
    assert ocr_model.active
    assert tsl_model.active
    ini.sync_models_epts()
    box_model.refresh_from_db()
    ocr_model.refresh_from_db()
    tsl_model.refresh_from_db()
    assert not box_model.active
    assert not ocr_model.active
    assert not tsl_model.active

@pytest.mark.django_db
def test_deactivate_missing_models_box_found(monkeypatch, box_model_dict, box_model, ocr_model, tsl_model):
    """Test initializer deactivate missing models."""
    def mock_load_ept_data(namespace):
        if namespace.endswith('.box_data'):
            return [box_model_dict]
        return []
    monkeypatch.setattr(ini, 'load_ept_data', mock_load_ept_data)

    assert box_model.active
    assert ocr_model.active
    assert tsl_model.active
    ini.sync_models_epts()
    box_model.refresh_from_db()
    ocr_model.refresh_from_db()
    tsl_model.refresh_from_db()
    assert box_model.active
    assert not ocr_model.active
    assert not tsl_model.active

def test_load_on_start_true(monkeypatch, mock_called):
    """Test initializer auto create models."""
    monkeypatch.setenv('LOAD_ON_START', 'true')
    monkeypatch.setattr(ini, 'init_most_used', mock_called)
    assert not hasattr(mock_called, 'called')
    ini.env_var_init()
    assert hasattr(mock_called, 'called')

def test_load_trie_unkwnown():
    """Test that the trie is not loaded when LOAD_TRIE is not 'true' or 'false'."""
    assert m.Language.get_loaded_trie() is None
    res = m.Language.load_trie('unknown')
    assert res is None

def test_load_trie(monkeypatch, language):
    """Test that the trie is loaded properly."""
    language.iso1 = 'test'
    language.save()
    language.refresh_from_db()
    assert language.LOADED_TRIE is None
    m.Language.load_model_src(language.iso1)
    assert language.LOADED_TRIE is not None

    trie = language.get_loaded_trie()
    assert trie is not None

    assert trie.search('ab') is True
    assert trie.search('cd') is True
    assert trie.search('abc') is False

    assert trie.get_freq('a') == 0.1
    assert trie.get_freq('b') == 0.2
    assert trie.get_freq('c') == 0.3
    assert trie.get_freq('ab') == -1e-4
