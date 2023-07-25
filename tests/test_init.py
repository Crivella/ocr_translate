"""Test environment initialization."""

import pytest

from ocr_translate import models as m
from ocr_translate import ocr_tsl
from ocr_translate.ocr_tsl import box, lang, ocr, tsl

pytestmark = pytest.mark.django_db

def test_init_most_used_clean(mock_loaders):
    """Test init_most_used with empty database."""
    ocr_tsl.init_most_used()
    assert box.BBOX_MODEL_OBJ is None
    assert ocr.OCR_MODEL_OBJ is None
    assert tsl.TSL_MODEL_OBJ is None
    assert lang.LANG_SRC is None
    assert lang.LANG_DST is None

def test_init_most_used_content(mock_loaders, language, ocr_box_model, ocr_model, tsl_model):
    """Test init_most_used with content in the database."""
    ocr_tsl.init_most_used()
    assert box.BBOX_MODEL_OBJ == ocr_box_model
    assert ocr.OCR_MODEL_OBJ == ocr_model
    assert tsl.TSL_MODEL_OBJ == tsl_model
    assert lang.LANG_SRC == language
    assert lang.LANG_DST == language

def test_init_most_used_more_content(mock_loaders, language_dict, image, option_dict, text):
    """Test init_most_used with more content in the database. Check that sorting is working."""
    # pylint: disable=unused-variable,too-many-locals
    dct1 = {k:v+'1' for k,v in language_dict.items()}
    dct2 = {k:v+'2' for k,v in language_dict.items()}
    dct3 = {k:v+'3' for k,v in language_dict.items()}
    lang1 = m.Language.objects.create(**dct1)
    lang2 = m.Language.objects.create(**dct2)
    lang3 = m.Language.objects.create(**dct3)

    ocr_box_model1 = m.OCRBoxModel.objects.create(name='test_model1/id')
    ocr_box_model2 = m.OCRBoxModel.objects.create(name='test_model2/id')

    ocr_model1 = m.OCRModel.objects.create(name='test_model1/id')
    ocr_model2 = m.OCRModel.objects.create(name='test_model2/id')

    tsl_model1 = m.TSLModel.objects.create(name='test_model1/id')
    tsl_model2 = m.TSLModel.objects.create(name='test_model2/id')

    box_run1 = m.OCRBoxRun.objects.create(
        model=ocr_box_model1, lang_src=lang1, image=image, options=option_dict
        )
    box_run2_1 = m.OCRBoxRun.objects.create(
        model=ocr_box_model2, lang_src=lang2, image=image, options=option_dict
        )
    box_run2_2 = m.OCRBoxRun.objects.create(
        model=ocr_box_model2, lang_src=lang2, image=image, options=option_dict
        )

    bbox = m.BBox.objects.create(image=image, l=1, b=2, r=3, t=4, from_ocr=box_run1)

    ocr_run1 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model1, options=option_dict, result=text
        )
    ocr_run2_1 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model2, options=option_dict, result=text
        )
    ocr_run2_2 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model2, options=option_dict, result=text
        )

    tsl_run1_1 = m.TranslationRun.objects.create(
        lang_src=lang2, lang_dst=lang3, text=text, model=tsl_model1, options=option_dict, result=text
        )
    tsl_run1_2 = m.TranslationRun.objects.create(
        lang_src=lang2, lang_dst=lang3, text=text, model=tsl_model1, options=option_dict, result=text
        )
    tsl_run2 = m.TranslationRun.objects.create(
        lang_src=lang1, lang_dst=lang1, text=text, model=tsl_model2, options=option_dict, result=text
        )

    ocr_tsl.init_most_used()

    assert lang.LANG_SRC == lang2
    assert lang.LANG_DST == lang3

    assert box.BBOX_MODEL_OBJ == ocr_box_model2
    assert ocr.OCR_MODEL_OBJ == ocr_model2
    assert tsl.TSL_MODEL_OBJ == tsl_model1

def test_auto_create_languages():
    """Test auto_create_languages."""
    ocr_tsl.auto_create_languages()

    assert m.Language.objects.count() > 50

    # Test settings of **kwargs
    jap = m.Language.objects.get(iso1='ja')
    assert jap.facebookM2M == 'ja'
    assert jap.break_chars is not None
    assert jap.ignore_chars is not None

def test_auto_create_models_nolang():
    """Test auto_create_models without creating languages before"""
    with pytest.raises(m.Language.DoesNotExist):
        ocr_tsl.auto_create_models()

def test_auto_create_models_lang():
    """Test auto_create_models after creating languages."""

    ocr_tsl.auto_create_languages()
    ocr_tsl.auto_create_models()

    assert m.OCRBoxModel.objects.count() > 0
    assert m.OCRModel.objects.count() > 0
    assert m.TSLModel.objects.count() > 0

    m2m = m.TSLModel.objects.get(name='facebook/m2m100_418M')
    eocr = m.OCRBoxModel.objects.get(name='easyocr')
    tess = m.OCRModel.objects.get(name='tesseract')

    # Test language code assignment
    assert m2m.language_format == 'facebookM2M'
    assert eocr.language_format == 'easyocr'
    assert tess.language_format == 'tesseract'
    # Test lang assignment for models (many-to-many)
    assert m2m.src_languages.count() > 10
    assert m2m.dst_languages.count() > 10
    assert eocr.languages.count() > 1
    assert tess.languages.count() > 1

# Not sure if this is testable as the ENV + function call is done at import time
# Even if i mock the function, reimporting the module is going to overwrite the mock
# def test_init_most_used_env_off(monkeypatch):
#     """Test init_most_used with LOAD_ON_START=False."""
#     called = False
#     def mock_register_called():
#         nonlocal called
#         called = True

#     monkeypatch.setenv('LOAD_ON_START', 'false')
#     monkeypatch.setattr(ocr_tsl, 'init_most_used', mock_register_called)

#     import ocr_translate.ocr_tsl  # pylint: disable=import-outside-toplevel

#     assert not called

# def test_init_most_used_env_on(monkeypatch):
#     """Test init_most_used with LOAD_ON_START=True."""
#     called = False
#     def mock_register_called():
#         print('--------------------------------called')
#         nonlocal called
#         called = True

#     monkeypatch.setenv('LOAD_ON_START', 'true')
#     monkeypatch.setattr(ocr_tsl, 'init_most_used', mock_register_called)

#     print('--------------------------------reloading')
#     # print('--------------------------------', sys.modules['ocr_translate.ocr_tsl'])
#     setattr(sys.modules['ocr_translate.ocr_tsl'], 'init_most_used', mock_register_called)
#     # importlib.reload(ocr_tsl)
#     import ocr_translate.ocr_tsl  # pylint: disable=import-outside-toplevel

#     assert called
