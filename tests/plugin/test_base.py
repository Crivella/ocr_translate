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
"""Tests for base plugin facility."""

import pytest

from ocr_translate import models as m


def test_base_from_entrypoint():
    """Test from_entrypoint method of BaseModel should `raise ValueError`."""
    with pytest.raises(ValueError):
        m.BaseModel.from_entrypoint('test_model_id')

@pytest.mark.django_db
def test_box_model_from_entrypoint_unknown(box_model: m.OCRBoxModel):
    """Test from_entrypoint method of OCRModel should `raise ValueError` if entrypoint is unknown."""
    with pytest.raises(ValueError, match=r'^Missing plugin: Entrypoint "test_entrypoint.box" not found.$'):
        m.OCRBoxModel.from_entrypoint(box_model.name)

@pytest.mark.django_db
def test_ocr_model_from_entrypoint_unknown(ocr_model: m.OCRModel):
    """Test from_entrypoint method of OCRModel should `raise ValueError` if entrypoint is unknown."""
    with pytest.raises(ValueError, match=r'^Missing plugin: Entrypoint "test_entrypoint.ocr" not found.$'):
        m.OCRModel.from_entrypoint(ocr_model.name)

@pytest.mark.django_db
def test_tsl_model_from_entrypoint_unknown(tsl_model: m.TSLModel):
    """Test from_entrypoint method of OCRModel should `raise ValueError` if entrypoint is unknown."""
    with pytest.raises(ValueError, match=r'^Missing plugin: Entrypoint "test_entrypoint.tsl" not found.$'):
        m.TSLModel.from_entrypoint(tsl_model.name)

@pytest.mark.django_db
def test_valid_entrypoint(monkeypatch, box_model: m.OCRBoxModel):
    """Test that valid entrypoint works."""
    monkeypatch.setattr(
        m, 'entry_points',
        lambda *args, **kwargs: [o,],
        )

    class Obj(): # pylint: disable=missing-class-docstring
        def __init__(self):
            self.called = False
            self.called_name = None

        @property
        def objects(self): # pylint: disable=missing-function-docstring
            class A(): # pylint: disable=missing-class-docstring,invalid-name
                pass
            new = A()
            new.get = self.get # pylint: disable=attribute-defined-outside-init
            return new

        def get(self, name): # pylint: disable=missing-function-docstring
            self.called = True
            self.called_name = name
            return name

        def load(self): # pylint: disable=missing-function-docstring
            return self

    o = Obj() # pylint: disable=invalid-name

    m.OCRBoxModel.from_entrypoint(box_model.name)

    assert o.called
    assert o.called_name == box_model.name

@pytest.mark.django_db
def test_box_load_not_implemented(box_model: m.OCRBoxModel):
    """Test that load method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        box_model.load()

@pytest.mark.django_db
def test_box_unload_not_implemented(box_model: m.OCRBoxModel):
    """Test that unload method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        box_model.unload()

@pytest.mark.django_db
def test_ocr_non_pil_image(ocr_model: m.OCRModel):
    """Test that ocr method raises TypeError if image is not PIL.Image."""
    with pytest.raises(TypeError, match=r'^img should be PIL Image, but got <class \'str\'>$'):
        ocr_model.prepare_image('test_image')

@pytest.mark.django_db
def test_box_main_method_notimplemented(box_model: m.OCRBoxModel):
    """Test that ocr method raises TypeError if image is not PIL.Image."""
    with pytest.raises(NotImplementedError):
        box_model._box_detection('test_image') # pylint: disable=protected-access

@pytest.mark.django_db
def test_ocr_main_method_notimplemented(ocr_model: m.OCRModel):
    """Test that ocr method raises TypeError if image is not PIL.Image."""
    with pytest.raises(NotImplementedError):
        ocr_model._ocr('test_image') # pylint: disable=protected-access

@pytest.mark.django_db
def test_tsl_main_method_notimplemented(tsl_model: m.TSLModel):
    """Test that ocr method raises TypeError if image is not PIL.Image."""
    with pytest.raises(NotImplementedError):
        tsl_model._translate('src_text', 'src_lang', 'dst_lang') # pylint: disable=protected-access
