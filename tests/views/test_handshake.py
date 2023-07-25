"""Test django serverside views.handshake."""

import http.cookies

import pytest
from django.urls import reverse

from ocr_translate.ocr_tsl import box, lang, ocr, tsl

pytestmark = pytest.mark.django_db

def test_handshake_clean_empty(client):
    """Test handshake."""
    url = reverse('ocr_translate:handshake')
    response = client.get(url)
    assert response.status_code == 200
    content = response.json()

    # Check that the csrf cookie is set
    assert isinstance(response.cookies, http.cookies.SimpleCookie)
    assert response.cookies['csrftoken']

    for key in ['Languages', 'BOXModels', 'OCRModels', 'TSLModels']:
        assert content[key] == []
    for key in ['box_selected', 'ocr_selected', 'tsl_selected']:
        assert content[key] == ''
    for key in ['lang_src', 'lang_dst']:
        assert content[key] == ''

def test_handshake_clean_content(client, language, ocr_box_model, ocr_model, tsl_model):
    """Test handshake with content in the database."""
    url = reverse('ocr_translate:handshake')
    response = client.get(url)
    assert response.status_code == 200
    content = response.json()

    assert content['Languages'] == ['ja']
    assert content['BOXModels'] == [ocr_box_model.name]
    assert content['OCRModels'] == [ocr_model.name]
    assert content['TSLModels'] == [tsl_model.name]

    for key in ['box_selected', 'ocr_selected', 'tsl_selected']:
        assert content[key] == ''
    for key in ['lang_src', 'lang_dst']:
        assert content[key] == ''

def test_handshake_clean_initialized(client, monkeypatch, language, ocr_box_model, tsl_model, ocr_model):
    """Test handshake with content + init."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(lang, 'LANG_DST', language)
    monkeypatch.setattr(box, 'BBOX_MODEL_OBJ', ocr_box_model)
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)

    url = reverse('ocr_translate:handshake')
    response = client.get(url)
    assert response.status_code == 200
    content = response.json()

    assert content['Languages'] == ['ja']
    assert content['BOXModels'] == [ocr_box_model.name]
    assert content['OCRModels'] == [ocr_model.name]
    assert content['TSLModels'] == [tsl_model.name]

    assert content['box_selected'] == ocr_box_model.name
    assert content['ocr_selected'] == ocr_model.name
    assert content['tsl_selected'] == tsl_model.name

    assert content['lang_src'] == 'ja'
    assert content['lang_dst'] == 'ja'
