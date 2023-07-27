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
"""Test base.py from ocr_tsl."""
# pylint: disable=redefined-outer-name

import importlib
from pathlib import Path

import pytest

from ocr_translate.ocr_tsl import huggingface


@pytest.fixture
def mock_loader():
    """Mock hugging face class with `from_pretrained` method."""
    class Loader():
        """Mocked class."""
        def from_pretrained(self, model_id: Path | str, cache_dir=None):
            """Mocked method."""
            if isinstance(model_id, Path):
                if not model_id.is_dir():
                    raise FileNotFoundError('Not in dir')
            elif isinstance(model_id, str):
                if cache_dir is None:
                    cache_dir = huggingface.root
                if not (cache_dir / f'models--{model_id.replace("/", "--")}').is_dir():
                    raise FileNotFoundError('Not in cache')

    return Loader()

def test_env_transformers_cache(monkeypatch):
    """Test that the TRANSFORMERS_CACHE environment variable is set."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', 'test')
    importlib.reload(huggingface)
    assert huggingface.root == Path('test')



def test_load_from_storage_dir_fail(monkeypatch, mock_loader, tmpdir):
    """Test low-level loading a huggingface model from storage (missing file)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    importlib.reload(huggingface)

    # Load is supposed to test direcotry first and than fallnack to cache
    # Exception should always be from not found in cache first
    with pytest.raises(FileNotFoundError, match='Not in cache'):
        huggingface.load(mock_loader, 'test/id')

def test_load_from_storage_dir_success(monkeypatch, mock_loader, tmpdir):
    """Test low-level loading a huggingface model from storage (success)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    importlib.reload(huggingface)

    ptr = tmpdir
    for pth in Path('test/id').parts:
        ptr = ptr.mkdir(pth)
    huggingface.load(mock_loader, 'test/id')

def test_load_from_storage_cache_success(monkeypatch, mock_loader, tmpdir):
    """Test low-level loading a huggingface model from storage (success)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    importlib.reload(huggingface)

    tmpdir.mkdir('models--test--id')
    huggingface.load(mock_loader, 'test/id')

def test_load_hugginface_model_invalide_type():
    """Test high-level loading a huggingface model. Request unkown entity."""
    with pytest.raises(ValueError, match=r'^Unknown request: .*'):
        huggingface.load_hugginface_model('test', ['invalid'])

def test_load_hugginface_model_return_none(monkeypatch):
    """Test high-level loading a huggingface model. Return None from load."""
    def mock_load(*args):
        """Mocked load function."""
        return None
    monkeypatch.setattr(huggingface, 'load', mock_load)

    with pytest.raises(ValueError, match=r'^Could not load model: .*'):
        huggingface.load_hugginface_model('test', ['model'])


@pytest.mark.parametrize('model_type', [
    'tokenizer',
    'ved_model',
    'model',
    'image_processor',
    'seq2seq'
])
def test_load_hugginface_model_success(monkeypatch, model_type):
    """Test high-level loading a huggingface model."""
    def mock_load(loader, *args):
        """Mocked load function."""
        assert loader == huggingface.mapping[model_type]
        class App():
            """Mocked huggingface class with `to` method."""
            def to(self, x): # pylint: disable=invalid-name,unused-argument
                """Mocked method."""
                return None
        return App()
    monkeypatch.setattr(huggingface, 'load', mock_load)

    loaded = huggingface.load_hugginface_model('test', [model_type])

    assert isinstance(loaded, dict)
    assert len(loaded) == 1
    assert model_type in loaded
