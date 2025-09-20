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
"""Test plugin manager."""

# pylint: disable=unused-argument,redefined-outer-name

import importlib
from collections import defaultdict
from importlib.metadata import EntryPoint

import pytest

from ocr_translate import entrypoint_manager as epm
from ocr_translate import models as m
from ocr_translate.ocr_tsl import cached_lists


@pytest.fixture
def mock_cls(request):
    """Mock class"""
    class MockCls:
        """Mock class"""
        get_counter = defaultdict(int)
        set_counter = defaultdict(int)
        call_counter = defaultdict(int)

        class DoesNotExist(Exception):
            """Mock DoesNotExist"""

        def __init__(self):
            self.prev68187471 = None

        def __getattr__(self, name):
            """Mock getattr"""
            if name == 'prev68187471':
                return object.__getattribute__(self, name)
            MockCls.get_counter[name] += 1
            self.prev68187471 = name
            return self  # pylint: disable=inconsistent-return-statements

        def __setattr__(self, name, value):
            """Mock setattr"""
            if name == 'prev68187471':
                object.__setattr__(self, name, value)
            MockCls.set_counter[name] += 1

        def __call__(self, *args, **kwargs):
            """Mock call"""
            if self.prev68187471 == 'get':
                if hasattr(request, 'param') and request.param == 'raise':
                    raise MockCls.DoesNotExist()
            MockCls.call_counter[self.prev68187471] += 1
            return self

    return MockCls

@pytest.fixture
def mock_models(monkeypatch, mock_cls):
    """Mock models"""
    box = mock_cls()
    ocr = mock_cls()
    tsl = mock_cls()
    monkeypatch.setattr(m, 'OCRBoxModel', box)
    monkeypatch.setattr(m, 'OCRModel', ocr)
    monkeypatch.setattr(m, 'TSLModel', tsl)
    importlib.reload(epm)
    return box, ocr, tsl

@pytest.fixture
def mock_ini(monkeypatch, mock_cls):
    """Mock models"""
    box = mock_cls()
    box.prev68187471 = 'box'
    ocr = mock_cls()
    ocr.prev68187471 = 'ocr'
    tsl = mock_cls()
    tsl.prev68187471 = 'tsl'
    importlib.reload(epm)

@pytest.fixture
def entrypoint1():
    """Mock entrypoint"""
    class MockEntryPoint(EntryPoint):
        """Mock entrypoint"""
        def load(self):
            """Mock load"""
            return {'name': 'name1', 'module': 'module1', 'attr': 'attr1'}
        @property
        def name(self):
            """Mock name"""
            return 'name1'
    return MockEntryPoint('name1', 'module1', 'attr1')


def test_get_group_entrypoints():
    """Test get_group_entrypoints"""
    res = epm.get_group_entrypoints('ocr_translate.box_data')
    assert isinstance(res, set)
    assert all(isinstance(ep, EntryPoint) for ep in res)

def test_manager_no_change_empty(monkeypatch, mock_models, mock_cls):
    """Test manager with no changes and no entrypoints"""
    monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: set())
    with epm.ep_manager():
        pass

    assert mock_cls.call_counter == {}

def test_manager_no_change_models(monkeypatch, mock_models, entrypoint1, mock_cls):
    """Test manager with no changes and entrypoints"""
    monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: {entrypoint1})
    with epm.ep_manager():
        pass

    assert mock_cls.call_counter['from_dct'] == 3

def test_manager_change_add(monkeypatch, mock_models, mock_cls, entrypoint1, mock_called):
    """Test manager with entrypoint added"""
    monkeypatch.setattr(cached_lists, 'refresh_model_cache', mock_called)
    monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: set())
    with epm.ep_manager():
        monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: {entrypoint1})

    assert mock_called.called

@pytest.mark.parametrize('mock_cls', ['raise'], indirect=True)
def test_manager_change_add_notexists(monkeypatch, mock_models, mock_ini, mock_cls, entrypoint1):
    """Test manager with entrypoint added"""
    monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: set())

    with epm.ep_manager():
        monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: {entrypoint1})

    assert mock_cls.call_counter['from_dct'] == 3

def test_manager_change_remove(monkeypatch, mock_models, mock_cls, entrypoint1, mock_called):
    """Test manager with entrypoint removed"""
    monkeypatch.setattr(cached_lists, 'refresh_model_cache', mock_called)
    monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: {entrypoint1})
    with epm.ep_manager():
        monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: set())
    assert mock_called.called
    assert mock_cls.call_counter['deactivate'] == 3

@pytest.mark.django_db
def test_manager_change_remove_loaded(monkeypatch, entrypoint1, mock_called, box_model_loaded):
    """Test manager with entrypoint removed"""
    monkeypatch.setattr(cached_lists, 'refresh_model_cache', lambda: None)
    monkeypatch.setattr(m.OCRBoxModel, 'unload_model', mock_called)
    box_model_loaded.name = 'name1'
    box_model_loaded.save()
    importlib.reload(epm)
    monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: {entrypoint1})
    with epm.ep_manager():
        monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: set())

    assert mock_called.called

@pytest.mark.parametrize('mock_cls', ['raise'], indirect=True)
def test_manager_change_remove_notexists(monkeypatch, mock_models, mock_cls, entrypoint1, mock_called):
    """Test manager with entrypoint removed"""
    monkeypatch.setattr(cached_lists, 'refresh_model_cache', mock_called)
    monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: {entrypoint1})
    with epm.ep_manager():
        monkeypatch.setattr(epm, 'get_group_entrypoints', lambda x: set())

    assert mock_called.called
    assert mock_cls.call_counter['save'] == 0
    assert mock_cls.set_counter['active'] == 0
