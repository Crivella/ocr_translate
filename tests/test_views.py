"""Test django serverside veiws."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_handshake_clean_empty(client):
    """Test handshake."""
    url = reverse('ocr_translate:handshake')
    response = client.get(url)
    assert response.status_code == 200
    content = response.json()

    assert content['Languages'] == []
    assert content['BOXModels'] == []
    assert content['OCRModels'] == []
    assert content['TSLModels'] == []

    assert content['box_selected'] == ''
    assert content['ocr_selected'] == ''
    assert content['tsl_selected'] == ''

    assert content['lang_src'] == ''
    assert content['lang_dst'] == ''

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

    assert content['box_selected'] == ''
    assert content['ocr_selected'] == ''
    assert content['tsl_selected'] == ''

    assert content['lang_src'] == ''
    assert content['lang_dst'] == ''

def test_handshake_used(client, ocr_box_run, ocr_run, tsl_run, ocr_box_model, tsl_model, ocr_model):
    """Test handshake with content + runs in the database."""
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
