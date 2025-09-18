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
"""Test dget_translationsjango serverside views.handshake."""
# pylint: disable=redefined-outer-name

import pytest
from django.urls import reverse

from ocr_translate import models as m
from ocr_translate.ocr_tsl import lang
from ocr_translate.views import get_default_options_from_cascade

pytestmark = pytest.mark.django_db

def test_cascade_action_wrong_list_name():
    """Test cascade action with wrong list name."""
    with pytest.raises(ValueError):
        get_default_options_from_cascade(['a'], 'test', '2')

def test_cascade_action_wrong_list_type():
    """Test cascade action with wrong list type."""
    with pytest.raises(TypeError):
        get_default_options_from_cascade([True], 'test', '2')

def test_cascade_action_none():
    """Test cascade action with none."""
    res = get_default_options_from_cascade([None], 'test', 2)
    assert res == 2

def test_cascade_action_base():
    """Test cascade action."""
    opt = m.OptionDict(options={'test': 1})
    res = get_default_options_from_cascade([opt], 'test', 2)
    assert res == 1

def test_cascade_action_default():
    """Test cascade action with default."""
    opt = m.OptionDict(options={})
    res = get_default_options_from_cascade([opt], 'test', 2)
    assert res == 2

def test_cascade_action_all(monkeypatch, box_model, ocr_model, tsl_model, language, language2):
    """Test cascade action multiple overrides."""
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(lang, 'LANG_DST', language2)

    opt1 = m.OptionDict.objects.create(options={'1': 1})
    opt2 = m.OptionDict.objects.create(options={'1': 2, '2': 2})
    opt3 = m.OptionDict.objects.create(options={'1': 3, '2': 3, '3': 3})
    opt4 = m.OptionDict.objects.create(options={'1': 4, '2': 4, '3': 4, '4': 4})
    opt5 = m.OptionDict.objects.create(options={'1': 5, '2': 5, '3': 5, '4': 5, '5': 5})

    box_model.default_options = opt1
    ocr_model.default_options = opt2
    tsl_model.default_options = opt3
    language.default_options = opt4
    language2.default_options = opt5

    lst = ['box_model', 'ocr_model', 'tsl_model', 'lang_src', 'lang_dst']
    lst.reverse()

    assert get_default_options_from_cascade(lst, '1', 6) == 1
    assert get_default_options_from_cascade(lst, '2', 6) == 2
    assert get_default_options_from_cascade(lst, '3', 6) == 3
    assert get_default_options_from_cascade(lst, '4', 6) == 4
    assert get_default_options_from_cascade(lst, '5', 6) == 5
    assert get_default_options_from_cascade(lst, '6', 6) == 6




def test_get_translations_nonget(client):
    """Test get_translations with non GET request."""
    url = reverse('ocr_translate:get_active_options')
    response = client.post(url)
    assert response.status_code == 405

def test_get_translations_params(client):
    """Test get_translations with GET request with non recognized attribute."""
    url = reverse('ocr_translate:get_active_options')
    response = client.get(url, {'test': 1})

    assert response.status_code == 400

def test_get_translations_noinit(client):
    """Test get_translations with GET request with non recognized attribute."""
    url = reverse('ocr_translate:get_active_options')
    response = client.get(url)

    assert response.status_code == 200
    assert response.json() == {'options': {'box_model': {}, 'ocr_model': {}, 'tsl_model': {}}}

def test_get_translations_init(client, monkeypatch, box_model_loaded):
    """Test get_translations with GET request with non recognized attribute."""
    # opt = m.OptionDict.objects.create(options={'test': 1})
    # monkeypatch.setattr(box_model, 'default_options', opt)
    dct = {'test': {
        'type': int, 'default': 1, 'description': 'test'
        }}
    monkeypatch.setattr(box_model_loaded, 'ALLOWED_OPTIONS', dct)
    url = reverse('ocr_translate:get_active_options')
    response = client.get(url)
    dct['test']['type'] = 'int'

    assert response.status_code == 200
    assert response.json() == {'options': {'box_model': dct, 'ocr_model': {}, 'tsl_model': {}}}

def test_get_translations_init_override_no(client, monkeypatch, box_model_loaded):
    """Test get_translations with GET request with non recognized attribute."""
    opt, _ = m.OptionDict.objects.get_or_create(options={})
    monkeypatch.setattr(box_model_loaded, 'default_options', opt)
    dct = {'test': {
        'type': int, 'default': ('cascade', ['box_model'], 1), 'description': 'test'
        }}
    monkeypatch.setattr(box_model_loaded, 'ALLOWED_OPTIONS', dct)
    url = reverse('ocr_translate:get_active_options')
    response = client.get(url)
    dct['test']['type'] = 'int'
    dct['test']['default'] = 1

    assert response.status_code == 200
    assert response.json() == {'options': {'box_model': dct, 'ocr_model': {}, 'tsl_model': {}}}

def test_get_translations_init_override_yes(client, monkeypatch, box_model_loaded):
    """Test get_translations with GET request with non recognized attribute."""
    opt = m.OptionDict.objects.create(options={'test': 2})
    monkeypatch.setattr(box_model_loaded, 'default_options', opt)
    dct = {'test': {
        'type': int, 'default': ('cascade', ['box_model'], 1), 'description': 'test'
        }}
    monkeypatch.setattr(box_model_loaded, 'ALLOWED_OPTIONS', dct)
    url = reverse('ocr_translate:get_active_options')
    response = client.get(url)
    dct['test']['type'] = 'int'
    dct['test']['default'] = 2

    assert response.status_code == 200
    assert response.json() == {'options': {'box_model': dct, 'ocr_model': {}, 'tsl_model': {}}}

def test_get_translations_init_override_invalid(client, monkeypatch, box_model_loaded):
    """Test get_translations with GET request with non recognized attribute."""
    dct = {'test': {
        'type': int, 'default': ('random_action', ['box_model'], 1), 'description': 'test'
        }}
    monkeypatch.setattr(box_model_loaded, 'ALLOWED_OPTIONS', dct)
    url = reverse('ocr_translate:get_active_options')
    with pytest.raises(ValueError):
        client.get(url)
