"""Test django serverside views.handshake."""
# pylint: disable=redefined-outer-name


import pytest
from django.urls import reverse

from ocr_translate import views

pytestmark = pytest.mark.django_db

@pytest.fixture()
def post_kwargs(text):
    """Data for POST request."""
    return {
        'data': {
            'text': text.text,
        },
        'content_type': 'application/json',
    }

def test_run_tsl_nonpost(client):
    """Test run_tsl with non POST request."""
    url = reverse('ocr_translate:run_tsl')
    response = client.get(url)
    assert response.status_code == 405

def test_run_tsl_post_noheader(client):
    """Test run_tsl with POST request without content/type."""
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url)

    assert response.status_code == 400

@pytest.mark.parametrize('remove_key', ['text'])
def test_run_tsl_post_missing_required(client, post_kwargs, remove_key):
    """Test run_tsl with POST request missing required field."""
    del post_kwargs['data'][remove_key]
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_run_tsl_post_invalid_data(client, post_kwargs):
    """Test run_tsl with POST request with non recognized field."""
    post_kwargs['data']['invalid_field'] = 'test'
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_run_tsl_post_valid(client, monkeypatch, post_kwargs):
    """Test run_tsl with POST request with valid data."""
    def mock_tsl_run(text, *args, **kwargs):
        """Mock translate."""
        yield text
    monkeypatch.setattr(views, 'tsl_run', mock_tsl_run)
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200
    content = response.json()

    assert content['text'] == post_kwargs['data']['text']
