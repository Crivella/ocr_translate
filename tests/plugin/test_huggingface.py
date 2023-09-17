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

from pathlib import Path

import pytest

from ocr_translate import models as m
from ocr_translate.plugins import hugginface

pytestmark = pytest.mark.django_db

@pytest.fixture()
def ved_model(language):
    """OCRModel database object."""
    model_dict = {
        'name': 'test_ved',
        'language_format': 'iso1',
        'entrypoint': 'hugginface.ved'
    }

    entrypoint = model_dict.pop('entrypoint')
    res = m.OCRModel.objects.create(**model_dict)
    res.entrypoint = entrypoint
    res.languages.add(language)
    res.save()

    return hugginface.HugginfaceVEDModel.objects.get(name = res.name)

@pytest.fixture()
def s2s_model(language):
    """OCRModel database object."""
    model_dict = {
        'name': 'test_seq2seq',
        'language_format': 'iso1',
        'entrypoint': 'hugginface.seq2seq'
    }

    entrypoint = model_dict.pop('entrypoint')
    res = m.TSLModel.objects.create(**model_dict)
    res.entrypoint = entrypoint
    res.src_languages.add(language)
    res.dst_languages.add(language)
    res.save()

    return hugginface.HugginfaceSeq2SeqModel.objects.get(name = res.name)



@pytest.fixture
def mock_loader(monkeypatch):
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
                    cache_dir = hugginface.EnvMixin().root
                if not (cache_dir / f'models--{model_id.replace("/", "--")}').is_dir():
                    raise FileNotFoundError('Not in cache')

            class A(): # pylint: disable=invalid-name
                """Mocked huggingface class with `to` method."""
                def to(self, dev): # pylint: disable=invalid-name,unused-argument,missing-function-docstring
                    pass
            return A()

    monkeypatch.setattr(hugginface.Loaders, 'mapping', {
        'tokenizer': Loader(),
        'seq2seq': Loader(),
        'model': Loader(),
        'ved_model': Loader(),
        'image_processor': Loader(),
    })

    # return Loader()

def test_env_transformers_cache(monkeypatch):
    """Test that the TRANSFORMERS_CACHE environment variable is set."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', 'test')
    mixin = hugginface.EnvMixin()
    assert mixin.root == Path('test')

def test_env_transformers_cpu(monkeypatch):
    """Test that the DEVICE environment variable is cpu."""
    monkeypatch.setenv('DEVICE', 'cpu')
    mixin = hugginface.EnvMixin()
    assert mixin.dev == 'cpu'

def test_env_transformers_cuda(monkeypatch):
    """Test that the DEVICE environment variable is cuda."""
    monkeypatch.setenv('DEVICE', 'cuda')
    mixin = hugginface.EnvMixin()
    assert mixin.dev == 'cuda'


def test_load_hugginface_model_invalide_type():
    """Test high-level loading a huggingface model. Request unkown entity."""
    with pytest.raises(ValueError, match=r'^Unknown request: .*'):
        hugginface.Loaders.load('test', ['invalid'], 'root')

def test_load_hugginface_model_return_none(monkeypatch):
    """Test high-level loading a huggingface model. Return None from load."""
    def mock_load(*args):
        """Mocked load function."""
        return None
    monkeypatch.setattr(hugginface.Loaders, '_load', mock_load)

    with pytest.raises(ValueError, match=r'^Could not load model: .*'):
        hugginface.Loaders.load('test', ['model'], 'root')

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
        assert loader == hugginface.Loaders.mapping[model_type]
        class App():
            """Mocked huggingface class with `to` method."""
            def to(self, x): # pylint: disable=invalid-name,unused-argument
                """Mocked method."""
                return None
        return App()
    monkeypatch.setattr(hugginface.Loaders, '_load', mock_load)

    loaded = hugginface.Loaders.load('test', [model_type], 'root')

    assert isinstance(loaded, dict)
    assert len(loaded) == 1
    assert model_type in loaded

####################################################################################
def test_load_from_storage_dir_fail(monkeypatch, mock_loader, tmpdir, ved_model):
    """Test low-level loading a huggingface model from storage (missing file)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    # Reload to make ENV effective
    ved_model = hugginface.HugginfaceVEDModel.objects.get(name = ved_model.name)

    # Load is supposed to test direcotry first and than fallnack to cache
    # Exception should always be from not found in cache first
    with pytest.raises(FileNotFoundError, match='Not in cache'):
        ved_model.load()

def test_load_from_storage_dir_success(monkeypatch, mock_loader, tmpdir, ved_model):
    """Test low-level loading a huggingface model from storage (success)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    # Reload to make ENV effective
    ved_model = hugginface.HugginfaceVEDModel.objects.get(name = ved_model.name)

    ptr = tmpdir
    for pth in Path(ved_model.name).parts:
        ptr = ptr.mkdir(pth)
    ved_model.load()

def test_load_from_storage_cache_success(monkeypatch, mock_loader, tmpdir, ved_model):
    """Test low-level loading a huggingface model from storage (success)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    # Reload to make ENV effective
    ved_model = hugginface.HugginfaceVEDModel.objects.get(name = ved_model.name)

    tmpdir.mkdir('models--' + ved_model.name.replace('/', '--'))
    ved_model.load()

def test_unload_from_loaded_ved(monkeypatch, tmpdir, ved_model):
    """Test unload box model with cpu."""
    monkeypatch.setattr(ved_model, 'model', '1')
    monkeypatch.setattr(ved_model, 'tokenizer', '1')

    ved_model.unload()
    assert ved_model.model is None
    assert ved_model.tokenizer is None

def test_unload_cpu(monkeypatch, mock_called, ved_model):
    """Test unload box model with cpu."""
    monkeypatch.setattr(hugginface.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(ved_model, 'dev', 'cpu')

    ved_model.unload()
    assert not hasattr(mock_called, 'called')

def test_unload_cuda(monkeypatch, mock_called, ved_model):
    """Test unload box model with cuda."""
    monkeypatch.setattr(hugginface.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(ved_model, 'dev', 'cuda')

    ved_model.unload()
    assert hasattr(mock_called, 'called')

# def test_pipeline_invalide_image(monkeypatch, hf_ved_model):
#     """Test ocr pipeline with invalid image."""
#     monkeypatch.setattr(hf_ved_model, 'model', '1')
#     monkeypatch.setattr(hf_ved_model, 'tokenizer', '1')
#     monkeypatch.setattr(hf_ved_model, 'image_processor', '1')
#     with pytest.raises(TypeError, match=r'^img should be PIL Image.*'):
#         hf_ved_model._ocr('invalid_image', 'ja') # pylint: disable=protected-access

def test_pipeline_notinit_ved(ved_model):
    """Test tsl pipeline with not initialized model."""
    with pytest.raises(RuntimeError, match=r'^Model not loaded$'):
        ved_model._ocr('image') # pylint: disable=protected-access

def test_pipeline_hugginface(
        image_pillow, mock_ocr_preprocessor, mock_ocr_tokenizer, mock_ocr_model, monkeypatch, ved_model):
    """Test ocr pipeline with hugginface model."""
    lang = 'ja'

    monkeypatch.setattr(ved_model, 'image_processor', mock_ocr_preprocessor(ved_model.name))
    monkeypatch.setattr(ved_model, 'tokenizer', mock_ocr_tokenizer(ved_model.name))
    monkeypatch.setattr(ved_model, 'model', mock_ocr_model(ved_model.name))

    res = ved_model._ocr(image_pillow, lang) # pylint: disable=protected-access

    assert res == 'abcde'

def test_pipeline_hugginface_cuda(
        image_pillow, mock_ocr_preprocessor, mock_ocr_tokenizer, mock_ocr_model, monkeypatch, ved_model):
    """Test ocr pipeline with hugginface model and cuda."""
    lang = 'ja'

    monkeypatch.setattr(ved_model, 'dev', 'cuda')
    monkeypatch.setattr(ved_model, 'image_processor', mock_ocr_preprocessor(ved_model.name))
    monkeypatch.setattr(ved_model, 'tokenizer', mock_ocr_tokenizer(ved_model.name))
    monkeypatch.setattr(ved_model, 'model', mock_ocr_model(ved_model.name))

    res = ved_model._ocr(image_pillow, lang) # pylint: disable=protected-access

    assert res == 'abcde'

####################################################################################
def test_get_mnt_wrong_options():
    """Test get_mnt with wrong options."""
    with pytest.raises(ValueError, match=r'^min_max_new_tokens must be less than max_max_new_tokens$'):
        hugginface.get_mnt(10, {'min_max_new_tokens': 20, 'max_max_new_tokens': 10})

def test_load_from_storage_dir_fail_s2s(monkeypatch, mock_loader, tmpdir, s2s_model):
    """Test low-level loading a huggingface model from storage (missing file)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    # Reload to make ENV effective
    s2s_model = hugginface.HugginfaceSeq2SeqModel.objects.get(name = s2s_model.name)

    # Load is supposed to test direcotry first and than fallnack to cache
    # Exception should always be from not found in cache first
    with pytest.raises(FileNotFoundError, match='Not in cache'):
        s2s_model.load()

def test_load_from_storage_dir_success_s2s(monkeypatch, mock_loader, tmpdir, s2s_model):
    """Test low-level loading a huggingface model from storage (success)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    # Reload to make ENV effective
    s2s_model = hugginface.HugginfaceSeq2SeqModel.objects.get(name = s2s_model.name)

    ptr = tmpdir
    for pth in Path(s2s_model.name).parts:
        ptr = ptr.mkdir(pth)
    s2s_model.load()

def test_load_from_storage_cache_success_s2s(monkeypatch, mock_loader, tmpdir, s2s_model):
    """Test low-level loading a huggingface model from storage (success)."""
    monkeypatch.setenv('TRANSFORMERS_CACHE', str(tmpdir))
    # Reload to make ENV effective
    s2s_model = hugginface.HugginfaceSeq2SeqModel.objects.get(name = s2s_model.name)

    tmpdir.mkdir('models--' + s2s_model.name.replace('/', '--'))
    s2s_model.load()

def test_unload_from_loaded_s2s(monkeypatch, tmpdir, s2s_model):
    """Test unload box model with cpu."""
    monkeypatch.setattr(s2s_model, 'model', '1')
    monkeypatch.setattr(s2s_model, 'tokenizer', '1')

    s2s_model.unload()
    assert s2s_model.model is None
    assert s2s_model.tokenizer is None

def test_unload_cpu_s2s(monkeypatch, mock_called, s2s_model):
    """Test unload box model with cpu."""
    monkeypatch.setattr(hugginface.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(s2s_model, 'dev', 'cpu')

    s2s_model.unload()
    assert not hasattr(mock_called, 'called')

def test_unload_cuda_s2s(monkeypatch, mock_called, s2s_model):
    """Test unload box model with cuda."""
    monkeypatch.setattr(hugginface.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(s2s_model, 'dev', 'cuda')

    s2s_model.unload()
    assert hasattr(mock_called, 'called')

def test_pipeline_notinit_s2s(s2s_model):
    """Test tsl pipeline with not initialized model."""
    with pytest.raises(RuntimeError, match=r'^Model not loaded$'):
        s2s_model._translate('test', 'ja', 'en') # pylint: disable=protected-access

# def test_pipeline_wrong_type(monkeypatch, mock_tsl_tokenizer, s2s_model):
#     """Test tsl pipeline with wrong type."""
#     monkeypatch.setattr(s2s_model, 'tokenizer', mock_tsl_tokenizer(s2s_model.name))
#     with pytest.raises(TypeError, match=r'^Unsupported type for text:.*'):
#         s2s_model._translate(1, 'ja', 'en') # pylint: disable=protected-access

def test_pipeline_no_tokens(monkeypatch, mock_tsl_tokenizer, s2s_model):
    """Test tsl pipeline with no tokens generated from pre_tokenize."""
    # monkeypatch.setattr(s2s_model, 'pre_tokenize', lambda *args, **kwargs: [])
    monkeypatch.setattr(s2s_model, 'model', '1')
    monkeypatch.setattr(s2s_model, 'tokenizer', mock_tsl_tokenizer('test/id'))

    res = s2s_model._translate('', 'ja', 'en') # pylint: disable=protected-access

    assert res == ''

def test_pipeline_m2m(monkeypatch, mock_tsl_tokenizer, mock_tsl_model, s2s_model):
    """Test tsl pipeline with m2m model."""
    monkeypatch.setattr(hugginface, 'M2M100Tokenizer', mock_tsl_tokenizer)
    # Reload to make ENV effective
    s2s_model = hugginface.HugginfaceSeq2SeqModel.objects.get(name = s2s_model.name)
    monkeypatch.setattr(s2s_model, 'model', mock_tsl_model(s2s_model.name))
    monkeypatch.setattr(s2s_model, 'tokenizer', mock_tsl_tokenizer(s2s_model.name))

    s2s_model._translate(['1',], 'ja', 'en') # pylint: disable=protected-access

    assert s2s_model.tokenizer.called_get_lang_id is True


def test_pipeline(string, monkeypatch, mock_tsl_tokenizer, mock_tsl_model, mock_called, s2s_model):
    """Test tsl pipeline (also check that cache is not cleared in CPU mode)."""
    lang_src = 'ja'
    lang_dst = 'en'

    monkeypatch.setattr(s2s_model, 'model', mock_tsl_model(s2s_model.name))
    monkeypatch.setattr(s2s_model, 'tokenizer', mock_tsl_tokenizer(s2s_model.name))
    monkeypatch.setattr(hugginface.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(s2s_model, 'dev', 'cpu')

    res = s2s_model._translate([string,], lang_src, lang_dst) # pylint: disable=protected-access

    assert res == string
    assert s2s_model.tokenizer.model_id == s2s_model.name
    assert s2s_model.tokenizer.src_lang == lang_src

    assert not hasattr(mock_called, 'called')

def test_pipeline_clear_cache(monkeypatch, mock_tsl_tokenizer, mock_tsl_model, mock_called, s2s_model):
    """Test tsl pipeline with cuda should clear_cache."""
    lang_src = 'ja'
    lang_dst = 'en'

    monkeypatch.setattr(s2s_model, 'model', mock_tsl_model(s2s_model.name))
    monkeypatch.setattr(s2s_model, 'tokenizer', mock_tsl_tokenizer(s2s_model.name))
    monkeypatch.setattr(hugginface.torch.cuda, 'empty_cache', mock_called)
    monkeypatch.setattr(s2s_model, 'dev', 'cuda')

    s2s_model._translate(['test',], lang_src, lang_dst) # pylint: disable=protected-access

    assert hasattr(mock_called, 'called')



def test_pipeline_batch(batch_string, monkeypatch, mock_tsl_tokenizer, mock_tsl_model, s2s_model):
    """Test tsl pipeline with batched string."""
    lang_src = 'ja'
    lang_dst = 'en'

    monkeypatch.setattr(s2s_model, 'model', mock_tsl_model(s2s_model.name))
    monkeypatch.setattr(s2s_model, 'tokenizer', mock_tsl_tokenizer(s2s_model.name))

    batch_string = [[_] for _ in batch_string]
    res = s2s_model._translate(batch_string, lang_src, lang_dst) # pylint: disable=protected-access

    assert res == [_[0] for _ in batch_string]
    assert s2s_model.tokenizer.model_id == s2s_model.name
    assert s2s_model.tokenizer.src_lang == lang_src

@pytest.mark.parametrize(
    'options',
    [
        {},
        {'min_max_new_tokens': 30},
        {'max_max_new_tokens': 22},
        {'max_new_tokens': 15},
        {'max_new_tokens_ratio': 2}
    ],
    ids=[
        'default',
        'min_max_new_tokens',
        'max_max_new_tokens',
        'max_new_tokens',
        'max_new_tokens_ratio'
    ]
)
def test_pipeline_options(options, string, monkeypatch, mock_tsl_tokenizer, mock_tsl_model, s2s_model):
    """Test tsl pipeline with options."""
    lang_src = 'ja'
    lang_dst = 'en'

    monkeypatch.setattr(s2s_model, 'model', mock_tsl_model(s2s_model.name))
    monkeypatch.setattr(s2s_model, 'tokenizer', mock_tsl_tokenizer(s2s_model.name))

    min_max_new_tokens = options.get('min_max_new_tokens', 20)
    max_max_new_tokens = options.get('max_max_new_tokens', 512)
    ntok = string.replace('\n', ' ').count(' ') + 1

    string = m.TSLModel.pre_tokenize(string)
    if min_max_new_tokens > max_max_new_tokens:
        with pytest.raises(ValueError):
            s2s_model._translate(string, lang_src, lang_dst, options=options) # pylint: disable=protected-access
    else:
        s2s_model._translate(string, lang_src, lang_dst, options=options) # pylint: disable=protected-access

    mnt = hugginface.get_mnt(ntok, options)

    model = s2s_model.model

    assert model.options['max_new_tokens'] == mnt
