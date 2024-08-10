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
"""Tests ENVIROMENT VARIABLES initialization."""

import pytest
from django.db.utils import OperationalError

from ocr_translate import ocr_tsl as o


@pytest.fixture(autouse=True)
def init_no_fail(monkeypatch):
    """Initialize without fail."""
    monkeypatch.setattr(o, 'FAIL', False)

def test_oct_init_call_true(monkeypatch, mock_called):
    """Test call on env variable."""
    monkeypatch.setattr(o, 'FAIL', False)
    monkeypatch.setenv('TEST', 'True')

    assert not hasattr(mock_called, 'called')
    o.run_on_env('TEST', mock_called)
    assert hasattr(mock_called, 'called')
    assert not o.FAIL

def test_oct_init_call_false(monkeypatch, mock_called):
    """Test call on env variable."""
    monkeypatch.setenv('TEST', 'False')

    assert not hasattr(mock_called, 'called')
    o.run_on_env('TEST', mock_called)
    assert not hasattr(mock_called, 'called')
    assert not o.FAIL

def test_oct_init_call_notdef(mock_called):
    """Test call on env variable."""
    assert not hasattr(mock_called, 'called')
    o.run_on_env('TEST', mock_called)
    assert not hasattr(mock_called, 'called')
    assert not o.FAIL

def test_oct_init_call_raise(monkeypatch):
    """Test call on env variable."""
    monkeypatch.setenv('TEST', 'True')
    def func():
        raise OperationalError('Test')
    o.run_on_env('TEST', func)
    assert o.FAIL