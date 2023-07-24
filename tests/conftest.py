"""Fixtures for the tests."""

import numpy as np
import pytest
from PIL import Image

from ocr_translate import models as m


@pytest.fixture()
def language_dict():
    """Dict defining a language"""
    return {
        'name': 'Japanese',
        'iso1': 'ja',
        'iso2b': 'jpn',
        'iso2t': 'jpn',
        'iso3': 'jpn',
    }

@pytest.fixture()
def ocr_box_model_dict():
    """Dict defiining an OCRBoxModel"""
    return {
        'name': 'test_model/id',
        'language_format': 'iso1'
    }

@pytest.fixture()
def ocr_model_dict():
    """Dict defiining an OCRModel"""
    return {
        'name': 'test_model/id',
        'language_format': 'iso1'
    }

@pytest.fixture()
def tsl_model_dict():
    """Dict defiining a TSLModel"""
    return {
        'name': 'test_model/id',
        'language_format': 'iso1'
    }

# @pytest.fixture(autouse=True)
# def globaldb(db):
#     """Fixture to load db"""
#     print('------------Loading db')
#     yield
#     print('------------Unloading db')

@pytest.fixture()
def option_dict():
    """OptionDict database object."""
    return m.OptionDict.objects.create(options={})

@pytest.fixture()
def language(language_dict):
    """Language database object."""
    return m.Language.objects.create(**language_dict)

@pytest.fixture(scope='session')
def image_pillow():
    """Random Pillow image."""
    npimg = np.random.randint(0,255,(25,25,3), dtype=np.uint8)
    return Image.fromarray(npimg)

@pytest.fixture()
def image():
    """Image database object."""
    return m.Image.objects.create(md5='test_md5')

@pytest.fixture()
def text():
    """Text database object."""
    return m.Text.objects.create(text='test_text')

@pytest.fixture()
def ocr_box_model(language, ocr_box_model_dict):
    """OCRBoxModel database object."""
    res = m.OCRBoxModel.objects.create(**ocr_box_model_dict)
    res.languages.add(language)

    return res

@pytest.fixture()
def ocr_model(language, ocr_model_dict):
    """OCRModel database object."""
    res = m.OCRModel.objects.create(**ocr_model_dict)
    res.languages.add(language)

    return res

@pytest.fixture()
def tsl_model(language, tsl_model_dict):
    """TSLModel database object."""
    res = m.TSLModel.objects.create(**tsl_model_dict)
    res.src_languages.add(language)
    res.dst_languages.add(language)

    return res

@pytest.fixture()
def ocr_box_run(language, image, ocr_box_model, option_dict):
    """OCRBoxRun database object."""
    return m.OCRBoxRun.objects.create(lang_src=language, image=image, model=ocr_box_model, options=option_dict)


@pytest.fixture()
def bbox(language, image, ocr_box_run):
    """BBox database object."""
    return m.BBox.objects.create(image=image, l=1, b=2, r=3, t=4, from_ocr=ocr_box_run)
