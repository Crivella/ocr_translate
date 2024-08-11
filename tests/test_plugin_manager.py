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

# pylint: disable=missing-class-docstring,protected-access,missing-function-docstring,import-outside-toplevel

import json
from pathlib import Path

import pytest

from ocr_translate import plugin_manager as pm


@pytest.fixture()
def mock_log_called():
    """Mock funciton that logs called arguments over multiple cals."""
    class MockLogFunc:
        called_args = []
        called_kwargs = []
        def __call__(self, *args, **kwargs):
            MockLogFunc.called_args.append(args)
            MockLogFunc.called_kwargs.append(kwargs)
    return MockLogFunc

@pytest.fixture(autouse=True, scope='function')
def tmp_base_dir(tmp_path, monkeypatch):
    """Set the base directory to a temporary directory."""
    monkeypatch.setenv('OCT_BASE_DIR', str(tmp_path))
    return tmp_path

@pytest.fixture()
def device(monkeypatch):
    """Set the device environment variable."""
    value = '123abc'
    monkeypatch.setenv('DEVICE', value)
    return value

@pytest.fixture()
def mock_plugin_data(tmp_base_dir, monkeypatch, device):
    """Create a mock plugin data file."""
    mock_file = tmp_base_dir / 'plugins_data.json'
    monkeypatch.setattr(pm.resources, 'files', lambda x: tmp_base_dir)
    mock_data = [
        {
            'name': 'plugin1',
            'package': 'pkg-p1',
            'version': '1.0',
            'dependencies': [
                {'name': 'pkg1', 'version': '1.0'},
                {'name': 'pkg2', 'version': '2.0'},
                {'name': 'pkg4', 'version': '1.1', 'scope': pm.GENERIC_SCOPE},
                {'name': 'pkg4', 'version': '1.2', 'scope': device},
                {'name': 'pkg5', 'version': '1.1', 'system': 'windows'},
                {'name': 'pkg5', 'version': '1.2', 'system': 'linux'},
            ]
        },
        {
            'name': 'plugin2',
            'package': 'pkg-p2',
            'version': '1.1',
            'dependencies': [
                {'name': 'pkg1', 'version': '1.0'},
                {'name': 'pkg3', 'version': '2.0'},
            ]
        },
    ]
    with mock_file.open('w') as f:
        json.dump(mock_data, f)
    return mock_data

@pytest.fixture()
def mock_plugin_file(tmp_base_dir):
    """Create a mock plugin data file."""
    mock_file = tmp_base_dir / 'plugins.json'
    mock_data = ['plugin1', 'plugin2']
    with mock_file.open('w') as f:
        json.dump(mock_data, f)
    return mock_data

@pytest.fixture()
def mock_installed_file(tmp_base_dir, device):
    """Create a mock plugin data file."""
    plugin_dir = tmp_base_dir / 'plugins'
    mock_file = plugin_dir / 'installed.json'

    sp_generic = plugin_dir / pm.GENERIC_SCOPE
    sp_device = plugin_dir / device
    sp_generic.mkdir(parents=True, exist_ok=True)
    sp_device.mkdir(parents=True, exist_ok=True)

    files1 = ['test_file-1_1', 'test_file-1_2']
    dirs1 = ['test_dir-1_1', 'test_dir-1_2']
    files2 = ['test_file-2_1', 'test_file-2_2']
    dirs2 = ['test_dir-2_1', 'test_dir-2_2']

    for pth in files1:
        (sp_generic / pth).touch()
    for pth in dirs1:
        (sp_generic / pth).mkdir()
    for pth in files2:
        (sp_device / pth).touch()
    for pth in dirs2:
        (sp_device / pth).mkdir()

    mock_data = {
        f'{pm.GENERIC_SCOPE}::pkg1': {'files': [], 'dirs': []},
        f'{pm.GENERIC_SCOPE}::pkg2': {'files': [], 'dirs': []},
        f'{pm.GENERIC_SCOPE}::pkg5': {'files': [], 'dirs': []},
        f'{pm.GENERIC_SCOPE}::pkg4': {
            'version': '1.1',
            'files': files1,
            'dirs': dirs1,
        },
        f'{device}::pkg4': {
            'version': '1.2',
            'files': files2,
            'dirs': dirs2,
        },
    }

    with mock_file.open('w') as f:
        json.dump(mock_data, f)
    return mock_data

@pytest.fixture(autouse=True)
def mock_django_configs(monkeypatch):
    monkeypatch.setattr(pm.settings, 'INSTALLED_APPS', [])
    monkeypatch.setattr(pm.apps, 'populate', lambda x: None)

def test_manager_singleton():
    """Test that the manager is a singleton."""
    pmng1 = pm.PluginManager()
    pmng2 = pm.PluginManager()
    assert pmng1 is pmng2

def test_init_env_device(device):
    """Test plugin manager init with environment variables."""
    pmng = pm.PluginManager()
    assert pmng.device == device

def test_init_env_device_default(monkeypatch):
    """Test plugin manager init with environment variables."""
    pmng = pm.PluginManager()
    assert pmng.device == 'cpu'

def test_init_plugin_dir_creation(tmp_base_dir):
    """Test plugin manager creates OCT_BASE_DIR/plugins directory."""
    pm.PluginManager()
    assert tmp_base_dir.joinpath('plugins').exists()

def test_init_scopes(monkeypatch, device, tmp_base_dir):
    """Test plugin manager init scopes."""
    monkeypatch.setattr(pm.site, 'USER_BASE', None)
    monkeypatch.setattr(pm.site, 'USER_SITE', None)
    pmng = pm.PluginManager()
    assert pm.GENERIC_SCOPE in pmng.scopes
    assert device in pmng.scopes
    assert (tmp_base_dir / 'plugins' / pm.GENERIC_SCOPE).exists()
    assert (tmp_base_dir / 'plugins' / device).exists()

    import sys
    assert sys.path[0] == pmng.PLUGIN_SP[device].as_posix()
    assert sys.path[1] == pmng.PLUGIN_SP[pm.GENERIC_SCOPE].as_posix()

    import site
    assert site.USER_BASE == pmng.plugin_dir.as_posix()
    assert site.USER_SITE == pmng.PLUGIN_SP[pm.GENERIC_SCOPE].as_posix()

def test_plugin_data():
    """Test plugin manager loading plugin data  with real file."""
    pmng = pm.PluginManager()
    assert isinstance(pmng.plugins_data, list)

def test_plugin_data_nofile(monkeypatch, tmp_base_dir):
    """Test plugin manager loading plugin data with non-existent file."""
    monkeypatch.setattr(pm.resources, 'files', lambda x: tmp_base_dir)

    pmng = pm.PluginManager()
    assert isinstance(pmng.plugins_data, list)
    assert pmng.plugins_data == []

def test_plugin_data_mock(monkeypatch, mock_plugin_data, mock_called):
    """Test plugin manager loading plugin data with mock file."""
    pmng = pm.PluginManager()
    assert isinstance(pmng.plugins_data, list)
    assert pmng._plugin_data is not None
    assert pmng.plugins_data == mock_plugin_data

    # Test caching of file
    monkeypatch.setattr(pm.json, 'load', mock_called)
    pmng.plugins_data  # pylint: disable=pointless-statement
    assert not hasattr(mock_called, 'called')

def test_get_plugin_data_absent(mock_plugin_data):
    """Test plugin manager get data from known plugin."""
    pmng = pm.PluginManager()
    data = pmng.get_plugin_data(mock_plugin_data[0]['name'] + 'x')
    assert data == {}

def test_get_plugin_data_present(mock_plugin_data):
    """Test plugin manager get data from known plugin."""
    pmng = pm.PluginManager()
    data = pmng.get_plugin_data(mock_plugin_data[0]['name'])
    assert data['name'] == mock_plugin_data[0]['name']
    assert data['version'] == mock_plugin_data[0]['version']


def test_plugin_file_mock(monkeypatch, mock_plugin_file, mock_called):
    """Test plugin manager loading installed plugin list."""
    pmng = pm.PluginManager()
    assert isinstance(pmng.plugins, list)
    assert pmng.plugins == mock_plugin_file

    # Test caching of file
    monkeypatch.setattr(pm.json, 'load', mock_called)
    pmng.plugins  # pylint: disable=pointless-statement
    assert not hasattr(mock_called, 'called')

def test_plugin_file_mock_envdisabled(monkeypatch):
    """Test plugin manager loading installed plugin list disabled by env var."""
    class MockFile:
        called = False
        def exists(self):
            MockFile.called = True
            return True

    pmng = pm.PluginManager()
    monkeypatch.setenv('OCT_DISABLE_PLUGINS', '1')
    monkeypatch.setattr(pmng, 'plugin_list_file', MockFile())
    assert pmng.plugins == []
    assert not MockFile.called

def test_installed_filea_mock(monkeypatch, mock_installed_file, mock_called):
    """Test plugin manager loading installed pkgs list."""
    pmng = pm.PluginManager()
    assert isinstance(pmng.installed_pkgs, dict)
    assert pmng._installed is not None
    assert pmng.installed_pkgs == mock_installed_file

    # Test caching of file
    monkeypatch.setattr(pm.json, 'load', mock_called)
    pmng.installed_pkgs  # pylint: disable=pointless-statement
    assert not hasattr(mock_called, 'called')

def test_save_plugin_list(monkeypatch, mock_plugin_file, mock_called):
    """Test plugin manager saving installed plugin list."""
    pmng = pm.PluginManager()
    pmng._plugins = mock_plugin_file
    monkeypatch.setattr(pm.json, 'dump', mock_called)
    pmng.save_plugin_list()
    assert mock_called.called
    assert mock_called.args[0] == mock_plugin_file
    assert Path(mock_called.args[1].name) == pmng.plugin_list_file

def test_save_installed(monkeypatch, mock_installed_file, mock_called):
    """Test plugin manager saving installed pkgs list."""
    pmng = pm.PluginManager()
    pmng._installed = mock_installed_file
    monkeypatch.setattr(pm.json, 'dump', mock_called)
    pmng.save_installed()
    assert mock_called.called
    assert mock_called.args[0] == mock_installed_file
    assert Path(mock_called.args[1].name) == pmng.installed_file

def test_install_plugin_unknown(mock_plugin_data):
    """Test plugin manager installing a plugin unknown."""
    pmng = pm.PluginManager()
    name = mock_plugin_data[0]['name'] + 'x'
    with pytest.raises(ValueError):
        pmng.install_plugin(name)

def test_install_plugin_known(monkeypatch, mock_plugin_data, mock_log_called):
    """Test plugin manager installing a plugin known."""
    data = mock_plugin_data[0]
    name = data['name']
    pkg = data['package']
    ver = data['version']
    dps = data['dependencies']

    pmng = pm.PluginManager()
    monkeypatch.setattr(pmng, 'install_package', mock_log_called())

    assert name not in pmng.plugins
    assert name not in pm.settings.INSTALLED_APPS
    pmng.install_plugin(name)
    assert name in pmng.plugins
    assert name in pm.settings.INSTALLED_APPS

    def get_name_version():
        args =  mock_log_called.called_args.pop()
        kwargs = mock_log_called.called_kwargs.pop()
        pkg_name = kwargs.get('name', None)
        pkg_version = kwargs.get('version', None)
        if len(args) > 0:
            pkg_name = args[0]
        if len(args) > 1:
            pkg_version = args[1]

        return pkg_name, pkg_version

    assert get_name_version() == (pkg, ver)

    for dep in dps:
        assert get_name_version() == (dep['name'], dep['version'])

def test_install_plugin_new_and_existing(monkeypatch, mock_plugin_data, mock_called):
    """Test plugin manager installing a plugin new first and existing after."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pmng, '_install_plugin', lambda x: None)
    name = mock_plugin_data[0]['name']
    assert not pmng.plugin_list_file.exists()
    assert name not in pm.settings.INSTALLED_APPS
    pmng.install_plugin(name)
    assert name in pmng.plugins
    assert name in pm.settings.INSTALLED_APPS
    assert pmng.plugin_list_file.exists()

    monkeypatch.setattr(pmng, 'save_plugin_list', mock_called)
    pmng.install_plugin(name)
    assert not hasattr(mock_called, 'called')

def test_uninstall_plugin_notinstalled_plist(monkeypatch, mock_plugin_data, mock_called):
    """Test plugin manager removing plugins not present in plugin list."""
    name = mock_plugin_data[0]['name']

    pmng = pm.PluginManager()
    monkeypatch.setattr(pmng, 'uninstall_package', mock_called)
    pmng.uninstall_plugin(name)

    assert not hasattr(mock_called, 'called')

def test_uninstall_plugin_notinstalled_pkgs(monkeypatch, mock_plugin_data):
    """Test plugin manager removing plugins not present in installed files."""
    name = mock_plugin_data[0]['name']

    pmng = pm.PluginManager()
    monkeypatch.setattr(pmng, '_plugins', [name])
    with pytest.raises(ValueError):
        pmng.uninstall_plugin(name)

def test_uninstall_plugin_remove_single(monkeypatch, mock_plugin_data, mock_log_called, device):
    """Test plugin manager removing a single plugins."""
    name = mock_plugin_data[0]['name']
    pkg = mock_plugin_data[0]['package']

    pmng = pm.PluginManager()
    monkeypatch.setattr(pm.settings, 'INSTALLED_APPS', [name])
    monkeypatch.setattr(pmng, '_plugins', [name])
    monkeypatch.setattr(pmng, '_installed', {f'{pm.GENERIC_SCOPE}::{pkg}' : {}})
    monkeypatch.setattr(pmng, 'uninstall_package', mock_log_called())

    pmng.uninstall_plugin(name)

    assert mock_log_called.called_args.pop() == (f'{pm.GENERIC_SCOPE}::{pkg}',)
    assert (f'{pm.GENERIC_SCOPE}::pkg1',) in mock_log_called.called_args
    assert (f'{pm.GENERIC_SCOPE}::pkg2',) in mock_log_called.called_args
    assert (f'{pm.GENERIC_SCOPE}::pkg5',) in mock_log_called.called_args
    assert (f'{pm.GENERIC_SCOPE}::pkg4',) in mock_log_called.called_args
    assert (f'{device}::pkg4',) in mock_log_called.called_args

    assert pmng.plugins == []
    assert pm.settings.INSTALLED_APPS == []

def test_uninstall_plugin_remove_shared(monkeypatch, mock_plugin_data, mock_log_called, device):
    """Test plugin manager removing a plugin with shared dependencies."""
    name1 = mock_plugin_data[0]['name']
    name2 = mock_plugin_data[1]['name']
    pkg = mock_plugin_data[0]['package']

    pmng = pm.PluginManager()
    monkeypatch.setattr(pm.settings, 'INSTALLED_APPS', [name1, name2])
    monkeypatch.setattr(pmng, '_plugins', [name1, name2])
    monkeypatch.setattr(pmng, '_installed', {f'{pm.GENERIC_SCOPE}::{pkg}' : {}})
    monkeypatch.setattr(pmng, 'uninstall_package', mock_log_called())

    pmng.uninstall_plugin(name1)

    assert mock_log_called.called_args.pop() == (f'{pm.GENERIC_SCOPE}::{pkg}',)
    assert (f'{pm.GENERIC_SCOPE}::pkg1',) not in mock_log_called.called_args
    assert (f'{pm.GENERIC_SCOPE}::pkg2',) in mock_log_called.called_args
    assert (f'{pm.GENERIC_SCOPE}::pkg5',) in mock_log_called.called_args
    assert (f'{pm.GENERIC_SCOPE}::pkg4',) in mock_log_called.called_args
    assert (f'{device}::pkg4',) in mock_log_called.called_args

    assert pmng.plugins == [name2]
    assert pm.settings.INSTALLED_APPS == [name2]

# def test_install_package():
#     """Test plugin manager installing a package."""
#     assert False
#     pmng = pm.PluginManager()
#     name = 'test'
#     pmng.install_package(name)
#     assert name in pmng.installed_pkgs

# def test_uninstall_package():
#     """Test plugin manager uninstalling a package."""
#     assert False
#     pmng = pm.PluginManager()
#     name = 'test'
#     pmng.uninstall_package(name)
#     assert name not in pmng.installed_pkgs

def test_uninstall_package_notinstalled(monkeypatch, mock_called):
    """Test plugin manager uninstalling a package that is not installed."""
    class MockDict(dict):
        called = False
        def pop(self, *args):
            MockDict.called = True
    pmng = pm.PluginManager()
    monkeypatch.setattr(pmng, '_installed', MockDict())

    pmng.uninstall_package('test')
    assert not MockDict.called

def test_uninstall_package_installed(monkeypatch, mock_installed_file, mock_called):
    """Test plugin manager uninstalling a package ."""
    scope = pm.GENERIC_SCOPE
    name = f'{scope}::pkg4'
    pmng = pm.PluginManager()

    monkeypatch.setattr(pmng, 'save_installed', mock_called)

    sp_dir = pmng.PLUGIN_SP[scope]
    files = mock_installed_file[name]['files']
    dirs = mock_installed_file[name]['dirs']

    for pth in files:
        assert (sp_dir / pth).exists()
    for pth in dirs:
        assert (sp_dir / pth).exists()

    pmng.uninstall_package(name)

    assert name not in pmng.installed_pkgs
    for pth in files:
        assert not (sp_dir / pth).exists()
    for pth in dirs:
        assert not (sp_dir / pth).exists()
    assert mock_called.called
