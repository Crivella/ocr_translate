"""Test django serverside views.set_models."""
# pylint: disable=redefined-outer-name

import pytest
from django.urls import reverse

from ocr_translate.ocr_tsl import box, ocr, tsl

pytestmark = pytest.mark.django_db

@pytest.fixture()
def post_kwargs(ocr_box_model, tsl_model, ocr_model):
    """Data for POST request."""
    return {
        'data': {
            'box_model_id': ocr_box_model.name,
            'ocr_model_id': ocr_model.name,
            'tsl_model_id': tsl_model.name,
        },
        'content_type': 'application/json',
    }

def test_set_models_nonpost(client):
    """Test set_models with non POST request."""
    url = reverse('ocr_translate:set_models')
    response = client.get(url)
    assert response.status_code == 405

def test_set_models_post_noheader(client):
    """Test set_models with POST request without content/type."""
    url = reverse('ocr_translate:set_models')
    response = client.post(url)

    assert response.status_code == 400

def test_set_models_post_invalid_data(client, post_kwargs):
    """Test set_models with POST request  with non recognized field."""
    post_kwargs['data']['invalid_field'] = 'test'
    url = reverse('ocr_translate:set_models')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_set_models_post_valid(client, mock_loaders, post_kwargs, ocr_box_model, tsl_model, ocr_model):
    """Test set_models with POST valid request."""
    url = reverse('ocr_translate:set_models')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200

    assert box.BOX_MODEL_ID == ocr_box_model.name
    assert ocr.OBJ_MODEL_ID == ocr_model.name
    assert tsl.TSL_MODEL_ID == tsl_model.name
