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
"""Test django serverside views.handshake."""
# pylint: disable=redefined-outer-name

import base64
import hashlib
import io

import pytest
from django.urls import reverse

from ocr_translate import views

pytestmark = pytest.mark.django_db

@pytest.fixture()
def image_b64(image_pillow):
    """Base64 encoded image."""
    buffer = io.BytesIO()
    image_pillow.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

@pytest.fixture()
def image_md5(image_b64):
    """MD5 of image."""
    return hashlib.md5(image_b64.encode('utf-8')).hexdigest()

@pytest.fixture()
def post_kwargs(image_b64, image_md5):
    """Data for POST request."""
    return {
        'data': {
            'contents': image_b64,
            'md5': image_md5,
            'force': False,
            'options': {},
        },
        'content_type': 'application/json',
    }

def test_run_ocrtsl_nonpost(client):
    """Test run_ocrtsl with non POST request."""
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.get(url)
    assert response.status_code == 405

def test_run_ocrtsl_post_noheader(client, mock_loaded):
    """Test run_ocrtsl with POST request without content/type."""
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url)

    assert response.status_code == 400

@pytest.mark.parametrize('remove_key', ['md5'])
def test_run_ocrtsl_post_missing_required(client, post_kwargs, remove_key, mock_loaded):
    """Test run_ocrtsl with POST request missing required field."""
    del post_kwargs['data'][remove_key]
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_run_ocrtsl_post_invalid_data(client, post_kwargs, mock_loaded):
    """Test run_ocrtsl with POST request with non recognized field."""
    post_kwargs['data']['invalid_field'] = 'test'
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_run_ocrtsl_post_nocontent_force(client, post_kwargs, mock_loaded):
    """Test run_ocrtsl with POST request with no content but force."""
    post_kwargs['data']['force'] = True
    post_kwargs['data'].pop('contents')
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400
    assert response.json()['error'] == 'Cannot force ocr without contents'

def test_run_ocrtsl_post_wrong_md5(client, post_kwargs, mock_loaded):
    """Test run_ocrtsl with POST request with wrong md5."""
    post_kwargs['data']['md5'] = 'wrong_md5'
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400
    assert response.json()['error'] == 'md5 mismatch'

def test_run_ocrtsl_post_valid_lazy_success(client, monkeypatch, post_kwargs, mock_loaded):
    """Test run_ocrtsl with POST request with valid data. No contents -> lazy + success"""
    post_kwargs['data'].pop('contents')
    def mock_ocrtsl_lazy(*args, **kwargs):
        """Mock ocrtsl lazy pipeline."""
        return [{'ocr': 'test_ocr', 'tsl': 'test_tsl', 'box': (1,2,3,4)}]
    monkeypatch.setattr(views, 'ocr_tsl_pipeline_lazy', mock_ocrtsl_lazy)
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200
    content = response.json()

    assert isinstance(content, dict)
    result = content['result']
    assert len(result) == 1
    assert result[0]['ocr'] == 'test_ocr'
    assert result[0]['tsl'] == 'test_tsl'
    assert result[0]['box'] == [1,2,3,4]

def test_run_ocrtsl_post_valid_lazy_failure(client, monkeypatch, post_kwargs, mock_loaded):
    """Test run_ocrtsl with POST request with valid data. No contents -> lazy + fail"""
    post_kwargs['data'].pop('contents')
    def mock_ocrtsl_lazy(*args, **kwargs):
        """Mock ocrtsl lazy pipeline."""
        raise ValueError('test')
    monkeypatch.setattr(views, 'ocr_tsl_pipeline_lazy', mock_ocrtsl_lazy)
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 406

def test_run_ocrtsl_post_valid_work_fail_langnotloaded(client, monkeypatch, post_kwargs):
    """Test run_ocrtsl with POST request with valid data. With contents -> work + success"""
    def mock_ocrtsl_work(*args, **kwargs):
        """Mock ocrtsl work pipeline."""
        return [{'ocr': 'test_ocr', 'tsl': 'test_tsl', 'box': (1,2,3,4)}]
    monkeypatch.setattr(views, 'ocr_tsl_pipeline_work', mock_ocrtsl_work)
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 512

def test_run_ocrtsl_post_valid_work_fail_modelnotloaded(client, monkeypatch, mock_loaded_lang_only, post_kwargs):
    """Test run_ocrtsl with POST request with valid data. With contents -> work + success"""
    def mock_ocrtsl_work(*args, **kwargs):
        """Mock ocrtsl work pipeline."""
        return [{'ocr': 'test_ocr', 'tsl': 'test_tsl', 'box': (1,2,3,4)}]
    monkeypatch.setattr(views, 'ocr_tsl_pipeline_work', mock_ocrtsl_work)
    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 513

def test_run_ocrtsl_post_valid_work_success(client, monkeypatch, mock_loaded, post_kwargs):
    """Test run_ocrtsl with POST request with valid data. With contents -> work + success"""
    def mock_ocrtsl_work(*args, **kwargs):
        """Mock ocrtsl work pipeline."""
        return [{'ocr': 'test_ocr', 'tsl': 'test_tsl', 'box': (1,2,3,4)}]
    monkeypatch.setattr(views, 'ocr_tsl_pipeline_work', mock_ocrtsl_work)

    url = reverse('ocr_translate:run_ocrtsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200
    content = response.json()

    assert isinstance(content, dict)
    result = content['result']
    assert len(result) == 1
    assert result[0]['ocr'] == 'test_ocr'
    assert result[0]['tsl'] == 'test_tsl'
    assert result[0]['box'] == [1,2,3,4]
