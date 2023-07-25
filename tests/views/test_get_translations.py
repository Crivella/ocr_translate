"""Test dget_translationsjango serverside views.handshake."""
# pylint: disable=redefined-outer-name

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

@pytest.fixture()
def get_kwargs(text):
    """Data for POST request."""
    return {
        'text': text.text,
    }

def test_get_translations_nonget(client):
    """Test get_translations with non GET request."""
    url = reverse('ocr_translate:get_trans')
    response = client.post(url)
    assert response.status_code == 405

@pytest.mark.parametrize('remove_key', ['text'])
def test_get_translations_get_missing_required(client, get_kwargs, remove_key):
    """Test get_translations with GET request missing required attribute."""
    del get_kwargs[remove_key]
    url = reverse('ocr_translate:get_trans')
    response = client.get(url, get_kwargs)

    assert response.status_code == 400

def test_get_translations_get_invalid_data(client, get_kwargs):
    """Test get_translations with GET request with non recognized attribute."""
    get_kwargs['invalid_field'] = 'test'
    url = reverse('ocr_translate:get_trans')
    response = client.get(url)

    assert response.status_code == 400

def test_get_translations_get_notfound(client, get_kwargs):
    """Test get_translations with GET request with non recognized attribute."""
    get_kwargs['text'] = 'other text'
    url = reverse('ocr_translate:get_trans')
    response = client.get(url, get_kwargs)

    assert response.status_code == 404

def test_get_translations_get_valid_notslrun(client, get_kwargs):
    """Test get_translations with GET request with valid data. No tsl run."""
    url = reverse('ocr_translate:get_trans')
    response = client.get(url, get_kwargs)

    assert response.status_code == 200
    content = response.json()

    assert isinstance(content, dict)
    translations = content['translations']
    assert isinstance(translations, list)
    assert len(translations) == 0

def test_get_translations_get_valid_tslrun(client, get_kwargs, mock_loaded, tsl_run):
    """Test get_translations with GET request with valid data. Tsl run."""
    url = reverse('ocr_translate:get_trans')
    response = client.get(url, get_kwargs)

    assert response.status_code == 200
    content = response.json()

    assert isinstance(content, dict)
    translations = content['translations']
    assert isinstance(translations, list)
    assert len(translations) == 1
    assert translations[0]['text'] == tsl_run.result.text
    assert translations[0]['model'] == tsl_run.model.name
