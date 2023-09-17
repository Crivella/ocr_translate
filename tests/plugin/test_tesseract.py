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
"""Tests for ocr module."""
# pylint: disable=redefined-outer-name

from pathlib import Path

import pytest
import requests
from PIL import Image

from ocr_translate import models as m
from ocr_translate.plugins import tesseract

pytestmark = pytest.mark.django_db

@pytest.fixture()
def tesseract_model(language):
    """OCRModel database object."""
    tesseract_model_dict = {
        'name': 'tesseract',
        'language_format': 'iso1',
        'entrypoint': 'tesseract.ocr'
    }

    entrypoint = tesseract_model_dict.pop('entrypoint')
    res = m.OCRModel.objects.create(**tesseract_model_dict)
    res.entrypoint = entrypoint
    res.languages.add(language)
    res.save()

    return tesseract.TesseractOCRModel.objects.get(name = res.name)

@pytest.fixture()
def mock_content():
    """Mock the content of a requests.Response."""
    return b'content'

@pytest.fixture(autouse=True)
def mock_get(request, monkeypatch, mock_content):
    """Mock the get method of requests."""
    scode = getattr(request, 'param', {}).get('status_code', 200)
    content = getattr(request, 'param', {}).get('content', mock_content)

    def mock_get(*args, **kwargs):
        res = requests.Response()
        res.status_code = scode
        res._content = content # pylint: disable=protected-access

        return res

    monkeypatch.setattr(tesseract.requests, 'get', mock_get)

def test_download_model_env_disabled(monkeypatch, tesseract_model):
    """Test the download of a model from the environment variable."""
    monkeypatch.setenv('TESSERACT_ALLOW_DOWNLOAD', 'false')
    # Reload to make ENV effective
    tesseract_model = tesseract.TesseractOCRModel.objects.get(name = 'tesseract')

    with pytest.raises(ValueError, match=r'^TESSERACT_ALLOW_DOWNLOAD is false\. Downloading models is not allowed$'):
        tesseract_model.download_model('eng')

def test_download_model_env_enabled(monkeypatch, tmpdir, mock_content, tesseract_model):
    """Test the download of a model from the environment variable."""
    monkeypatch.setenv('TESSERACT_ALLOW_DOWNLOAD', 'true')
    monkeypatch.setenv('TESSERACT_PREFIX', str(tmpdir))
    # Reload to make ENV effective
    tesseract_model = tesseract.TesseractOCRModel.objects.get(name = 'tesseract')

    model = 'test'
    tesseract_model.download_model(model)
    tmpfile = tmpdir / f'{model}.traineddata'
    assert tmpfile.exists()
    with open(tmpfile, 'rb') as f:
        assert f.read() == mock_content

def test_download_already_exists(monkeypatch, tmpdir, mock_called, tesseract_model):
    """Test the download of a model from the environment variable."""
    monkeypatch.setattr(tesseract_model, 'download', True)
    monkeypatch.setattr(tesseract_model, 'data_dir', Path(tmpdir))
    monkeypatch.setattr(tesseract.requests, 'get', mock_called)

    model = 'test'
    tmpfile = tmpdir / f'{model}.traineddata'
    with tmpfile.open('w') as f:
        f.write('test')
    tesseract_model.download_model(model)

    assert not hasattr(mock_called, 'called')


@pytest.mark.parametrize('mock_get', [{'status_code': 404}], indirect=True)
def test_download_fail_request(monkeypatch, tmpdir, tesseract_model):
    """Test the download of a language with a normal+vertical model."""
    monkeypatch.setattr(tesseract_model, 'download', True)
    monkeypatch.setattr(tesseract_model, 'data_dir', Path(tmpdir))

    model = 'test'
    with pytest.raises(ValueError, match=r'^Could not download model for language.*'):
        tesseract_model.download_model(model)

def test_download_vertical(monkeypatch, tmpdir, tesseract_model):
    """Test the download of a language with a normal+vertical model."""
    monkeypatch.setattr(tesseract_model, 'download', True)
    monkeypatch.setattr(tesseract_model, 'data_dir', Path(tmpdir))

    model = tesseract_model.VERTICAL_LANGS[0]
    tesseract_model.download_model(model)

    tmpfile_h = tmpdir / f'{model}.traineddata'
    tmpfile_v = tmpdir / f'{model}_vert.traineddata'
    assert tmpfile_h.exists()
    assert tmpfile_v.exists()

def test_create_config(monkeypatch, tmpdir, tesseract_model):
    """Test the creation of the tesseract config file."""
    monkeypatch.setattr(tesseract_model, 'config', False)
    monkeypatch.setattr(tesseract_model, 'data_dir', Path(tmpdir))

    tesseract_model.create_config()

    assert tesseract_model.config is True
    pth = Path(tmpdir)
    assert (pth / 'configs').is_dir()
    assert (pth / 'configs' / 'tsv').is_file()
    with open(pth / 'configs' / 'tsv', encoding='utf-8') as f:
        assert f.read() == 'tessedit_create_tsv 1'

def test_create_config_many(monkeypatch, mock_called, tesseract_model):
    """Test that the creation of the tesseract config file happens only once."""
    monkeypatch.setattr(tesseract_model, 'config', False)

    monkeypatch.setattr(tesseract.Path, 'exists', lambda *args, **kwargs: True)
    monkeypatch.setattr(tesseract.Path, 'mkdir', lambda *args, **kwargs: None)
    tesseract_model.create_config()
    monkeypatch.setattr(tesseract.Path, 'mkdir', mock_called)
    tesseract_model.create_config()

    assert not hasattr(mock_called, 'called')

def test_tesseract_pipeline_nomodel(monkeypatch, mock_called, tmpdir, tesseract_model):
    """Test the tesseract pipeline."""
    mock_result = 'mock_ocr_result'
    def mock_tesseract(*args, **kwargs):
        return {'text': mock_result}
    monkeypatch.setattr(tesseract_model, 'config', True)
    monkeypatch.setattr(tesseract_model, 'download', True)
    monkeypatch.setattr(tesseract_model, 'data_dir', Path(tmpdir))

    monkeypatch.setattr(tesseract_model, 'download_model', mock_called)
    monkeypatch.setattr(tesseract, 'image_to_string', mock_tesseract)

    res = tesseract_model._ocr('image', 'lang') # pylint: disable=protected-access

    assert hasattr(mock_called, 'called')
    assert res == mock_result
    assert len(tmpdir.listdir()) == 0 # No config should be written and download is mocked

def test_tesseract_pipeline_noconfig(monkeypatch, mock_called, tmpdir, tesseract_model):
    """Test the tesseract pipeline."""
    mock_result = 'mock_ocr_result'
    def mock_tesseract(*args, **kwargs):
        return {'text': mock_result}
    monkeypatch.setattr(tesseract_model, 'config', False)
    monkeypatch.setattr(tesseract_model, 'download', True)
    monkeypatch.setattr(tesseract_model, 'data_dir', Path(tmpdir))

    monkeypatch.setattr(tesseract_model, 'create_config', mock_called)
    monkeypatch.setattr(tesseract_model, 'download_model', lambda *args, **kwargs: None)
    monkeypatch.setattr(tesseract, 'image_to_string', mock_tesseract)

    res = tesseract_model._ocr('image', 'lang') # pylint: disable=protected-access

    assert hasattr(mock_called, 'called')
    assert res == mock_result
    assert len(tmpdir.listdir()) == 0 # No file should be downloaded (lambda mocked) and config is mocked

@pytest.mark.parametrize('mock_called', [{'text': 0}], indirect=True)
def test_tesseract_pipeline_psm_horiz(monkeypatch, mock_called, tesseract_model):
    """Test the tesseract pipeline."""
    monkeypatch.setattr(tesseract_model, 'create_config', lambda *args, **kwargs: None)
    monkeypatch.setattr(tesseract_model, 'download_model', lambda *args, **kwargs: None)
    monkeypatch.setattr(tesseract, 'image_to_string', mock_called)

    tesseract_model._ocr('image', 'lang') # pylint: disable=protected-access

    assert hasattr(mock_called, 'called')
    assert '--psm 6' in mock_called.kwargs['config']

@pytest.mark.parametrize('mock_called', [{'text': 0}], indirect=True)
def test_tesseract_pipeline_psm_vert(monkeypatch, mock_called, tesseract_model):
    """Test the tesseract pipeline."""
    monkeypatch.setattr(tesseract_model, 'create_config', lambda *args, **kwargs: None)
    monkeypatch.setattr(tesseract_model, 'download_model', lambda *args, **kwargs: None)
    monkeypatch.setattr(tesseract, 'image_to_string', mock_called)

    image = Image.new('RGB', (100, 100))
    lang = tesseract_model.VERTICAL_LANGS[0]
    tesseract_model._ocr(image, lang) # pylint: disable=protected-access

    assert hasattr(mock_called, 'called')
    assert '--psm 5' in mock_called.kwargs['config']
