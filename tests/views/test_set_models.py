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
"""Test django serverside views.set_models."""
# pylint: disable=redefined-outer-name

import pytest
from django.urls import reverse

from ocr_translate import models as m

pytestmark = pytest.mark.django_db

@pytest.fixture()
def post_kwargs(box_model, tsl_model, ocr_model):
    """Data for POST request."""
    return {
        'data': {
            'box_model_id': box_model.name,
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

def test_set_models_post_fail_load(client, post_kwargs):
    """Test set_models with POST request with wrong model data (cause exceptio in load_XXX_model)."""
    post_kwargs['data']['box_model_id'] = 'invalid'

    url = reverse('ocr_translate:set_models')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_set_models_post_invalid_data(client, post_kwargs):
    """Test set_models with POST request  with non recognized field."""
    post_kwargs['data']['invalid_field'] = 'test'
    url = reverse('ocr_translate:set_models')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_set_models_post_valid(client, mock_loaders, post_kwargs, box_model, tsl_model, ocr_model):
    """Test set_models with POST valid request."""
    url = reverse('ocr_translate:set_models')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200

    assert m.OCRBoxModel.LOADED_MODEL == box_model
    assert m.OCRModel.LOADED_MODEL == ocr_model
    assert m.TSLModel.LOADED_MODEL == tsl_model

def test_set_models_post_valid_notall(client, mock_loaders, post_kwargs, tsl_model, ocr_model):
    """Test set_models with POST valid request."""
    url = reverse('ocr_translate:set_models')
    post_kwargs['data'].pop('box_model_id')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200

    assert m.OCRBoxModel.LOADED_MODEL is None
    assert m.OCRModel.LOADED_MODEL == ocr_model
    assert m.TSLModel.LOADED_MODEL == tsl_model
