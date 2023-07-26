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
"""Tests for the database models."""

import pytest

from ocr_translate.ocr_tsl import lang

pytestmark = pytest.mark.django_db

def test_get_lang_src(monkeypatch):
    """Test getting the source language."""
    monkeypatch.setattr(lang, 'LANG_SRC', 'test_lang_src')
    assert lang.get_lang_src() == 'test_lang_src'

def test_get_lang_dst(monkeypatch):
    """Test getting the destination language."""
    monkeypatch.setattr(lang, 'LANG_DST', 'test_lang_dst')
    assert lang.get_lang_dst() == 'test_lang_dst'

def test_load_lang_src(monkeypatch, language):
    """Test loading the source language."""
    monkeypatch.setattr(lang, 'LANG_SRC', None)
    lang.load_lang_src(language.iso1)
    assert lang.get_lang_src() == language

def test_load_lang_dst(monkeypatch, language):
    """Test loading the destination language."""
    monkeypatch.setattr(lang, 'LANG_DST', None)
    lang.load_lang_dst(language.iso1)
    assert lang.get_lang_dst() == language
