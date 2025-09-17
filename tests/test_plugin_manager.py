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
# pylint: disable=too-many-lines

import json
import threading
import time
from contextlib import nullcontext
from pathlib import Path

import pytest

from ocr_translate import entrypoint_manager as epm
from ocr_translate import plugin_manager as pm
from ocr_translate.ocr_tsl import initializers as ini


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

@pytest.fixture()
def mock_sprun():
    class MockSPrun:
        called = False
        args = []
        def __call__(self, *args, **kwargs):
            MockSPrun.called = True
            MockSPrun.args = args
            return self
        @property
        def stdout(self):
            return b'test'
        @property
        def stderr(self):
            return b'error!!'
    return MockSPrun

@pytest.fixture(autouse=True, scope='function')
def tmp_base_dir(tmp_path, monkeypatch):
    """Set the base directory to a temporary directory."""
    monkeypatch.setenv('OCT_BASE_DIR', str(tmp_path))
    return tmp_path

# Avoid running entrypoint manager together with plugin manager to test without DB access
# as reloading the apps does not play nice with `pytest.mark.django_db`
@pytest.fixture(autouse=True)
def mock_ep_manager(monkeypatch):
    """Mock the entrypoint manager."""
    monkeypatch.setattr(epm, 'ep_manager', nullcontext)

@pytest.fixture()
def disabled(monkeypatch):
    """Disable plugins."""
    monkeypatch.setenv('OCT_DISABLE_PLUGINS', '1')

@pytest.fixture()
def django_debug(monkeypatch):
    """Set the Django debug environment variable."""
    monkeypatch.setenv('DJANGO_DEBUG', 'true')

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

def test_get_safe_name():
    """Test that safe name returns a valid python variable name."""
    assert pm.get_safe_name('-') == '_min_'
    assert pm.get_safe_name('--') == '_min__min_'

@pytest.mark.parametrize('mock_called', ['safe_name'], indirect=True)
def test_overrides_decorator_noname(monkeypatch, mock_called):
    """Test that overrides decorator raises if no name is given."""
    monkeypatch.setattr(pm, 'get_safe_name', mock_called)
    @pm.install_overrides_decorator
    def test_func(*args, **kwargs):
        return args, kwargs

    with pytest.raises(ValueError):
        test_func('cls')

@pytest.mark.parametrize('mock_called', ['safe_name'], indirect=True)
def test_overrides_decorator_name_args(monkeypatch, mock_called):
    """Test that overrides decorator 2nd argument is a string passed to safe name."""
    monkeypatch.setattr(pm, 'get_safe_name', mock_called)
    @pm.install_overrides_decorator
    def test_func(*args, **kwargs):
        return args

    assert test_func('cls', 'name') == ('cls',)
    assert mock_called.args == ('name',)

def test_overrides_decorator_name_double():
    """Test that overrides decorator 2nd argument cant also be present in kwargs."""
    @pm.install_overrides_decorator
    def test_func(*args, **kwargs):
        return args

    with pytest.raises(TypeError):
        test_func('cls', 'name', name='123')

def test_overrides_decorator_other_double():
    """Test that overrides decorator 3nd and forth argument cant also be present in kwargs."""
    @pm.install_overrides_decorator
    def test_func(*args, **kwargs):
        return args

    args = ['cls', 'name', ]
    arg_names = ['version', 'extras', 'scope', 'system']
    for name in arg_names:
        args.append(name)
        with pytest.raises(TypeError):
            test_func(*args, **{name: '123'})

@pytest.mark.parametrize('mock_called', ['safe_name'], indirect=True)
def test_overrides_decorator_name_kwargs(monkeypatch, mock_called):
    """Test that overrides decorator 2nd argument is a string passed to safe name."""
    monkeypatch.setattr(pm, 'get_safe_name', mock_called)
    @pm.install_overrides_decorator
    def test_func(*args, **kwargs):
        return args, kwargs

    args, kwargs = test_func('cls', name='name')

    assert args == ('cls',)
    assert kwargs == {'name': 'name'}

def test_overrides_decorator_only_kwargs():
    """Test that overrides decorator only passes kwargs downstream beside class."""
    @pm.install_overrides_decorator
    def test_func(*args, **kwargs):
        return args

    assert test_func('cls', 'name', 3, somekw=1) == ('cls',)

def test_pip_install_raise_retries_ok(monkeypatch, mock_sprun, mock_called):
    """Test pip install with raise call."""
    attempts = 2
    def raise_func(*args, **kwargs):
        nonlocal attempts
        if attempts == 0:
            return mock_sprun()
        attempts -= 1
        exc = pm.subprocess.CalledProcessError(1, 'test')
        exc.stdout = b'test stdout'
        exc.stderr = b'test stderr'
        raise exc
    monkeypatch.setattr(pm.time, 'sleep', lambda x: None)  # No need to sleep for test
    monkeypatch.setattr(pm.subprocess, 'run', raise_func)
    monkeypatch.setattr(pm.logger, 'error', mock_called)

    # with pytest.raises(pm.subprocess.CalledProcessError):
    pm._pip_install('test', '.')
    assert mock_called.called
    # assert mock_called.args[0] == 'test stderr'

def test_pip_install_raise_retries_fail(monkeypatch, mock_sprun, mock_called):
    """Test pip install with raise call."""
    attempts = 5
    def raise_func(*args, **kwargs):
        nonlocal attempts
        if attempts == 0:
            return mock_sprun()
        attempts -= 1
        exc = pm.subprocess.CalledProcessError(1, 'test')
        exc.stdout = b'test stdout'
        exc.stderr = b'test stderr'
        raise exc
    monkeypatch.setattr(pm.time, 'sleep', lambda x: None)  # No need to sleep for test
    monkeypatch.setattr(pm.subprocess, 'run', raise_func)
    monkeypatch.setattr(pm.logger, 'error', mock_called)

    with pytest.raises(pm.subprocess.CalledProcessError):
        pm._pip_install('test', '.')
    assert mock_called.called
    assert mock_called.args[0] == 'test stderr'

def test_pip_install_extras_none(monkeypatch, mock_sprun):
    """Test pip install with no extras."""
    monkeypatch.setattr(pm.subprocess, 'run', mock_sprun())
    pm._pip_install('test', '.')
    assert mock_sprun.called
    assert mock_sprun.args[0][-1] == '--prefix=.'

def test_pip_install_extras_empty(monkeypatch, mock_sprun, mock_called):
    """Test pip install with no extras."""
    monkeypatch.setattr(pm.subprocess, 'run', mock_sprun())
    monkeypatch.setattr(pm.logger, 'error', mock_called)
    pm._pip_install('test', '.', [])
    assert mock_sprun.called
    assert mock_sprun.args[0][-1] == '--prefix=.'
    assert not hasattr(mock_called, 'called')

def test_pip_install_extras(monkeypatch, mock_sprun):
    """Test pip install with no extras."""
    monkeypatch.setattr(pm.subprocess, 'run', mock_sprun())
    pm._pip_install('test', '.', ['123'])
    assert mock_sprun.called
    assert mock_sprun.args[0][-1] == '123'

def test_manager_singleton():
    """Test that the manager is a singleton."""
    pmng1 = pm.PluginManager()
    pmng2 = pm.PluginManager()
    assert pmng1 is pmng2

def test_ensurepip_disabled(monkeypatch, disabled, mock_called):
    """Test plugin manager ensure_pip function with disabled form env."""
    monkeypatch.setattr(pm.subprocess, 'run', mock_called)
    pm.PluginManager()
    assert not hasattr(mock_called, 'called')

def test_ensurepip_success(monkeypatch, mock_called):
    """Test plugin manager ensure_pip function mocked success."""
    monkeypatch.setattr(pm.subprocess, 'run', mock_called)
    pm.PluginManager()
    assert mock_called.called

def test_ensurepip_fail(monkeypatch, mock_called):
    """Test plugin manager ensure_pip function mocked failure. Test that running subprocess.run on a non-existent
    file raises FileNotFoundError."""
    import functools
    import subprocess
    app = functools.partial(subprocess.run, ['thisfileshouldnotexist'])
    def mock_run(*args, **kwargs):
        app(*args[1:], **kwargs)
    monkeypatch.setattr(pm.subprocess, 'run', mock_run)
    with pytest.raises(FileNotFoundError):
        pm.PluginManager()

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

def test_init_scopes_disabled(monkeypatch, disabled, tmp_base_dir):
    """Test plugin manager init scopes."""
    monkeypatch.setattr(pm.site, 'USER_BASE', None)
    monkeypatch.setattr(pm.site, 'USER_SITE', None)
    pmng = pm.PluginManager()
    assert pm.GENERIC_SCOPE in pmng.scopes
    assert not (tmp_base_dir / 'plugins' / pm.GENERIC_SCOPE).exists()

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

def test_init_site_packages_removal(tmp_base_dir):
    """Test plugin manager init site packages removal."""
    sp1 = tmp_base_dir / 'plugins' / 'site-packages'
    sp2 = tmp_base_dir / 'plugins' / 'test1' / 'site-packages'
    sp3 = tmp_base_dir / 'plugins' / 'test1' / 'test2' / 'site-packages'
    sp1.mkdir(parents=True, exist_ok=True)
    sp2.mkdir(parents=True, exist_ok=True)
    sp3.mkdir(parents=True, exist_ok=True)
    pm.PluginManager()
    assert not sp1.exists()
    assert not sp2.exists()
    assert not sp3.exists()

def test_plugin_data():
    """Test plugin manager loading plugin data  with real file."""
    pmng = pm.PluginManager()
    assert isinstance(pmng.plugins_data, list)

def test_plugin_data_disabled(disabled):
    """Test plugin manager loading plugin data  with real file."""
    pmng = pm.PluginManager()
    assert isinstance(pmng.plugins_data, list)
    assert pmng._plugin_data is None

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

def test_plugin_file_mock_disabled(monkeypatch, disabled, mock_plugin_file, mock_called):
    """Test plugin manager loading installed plugin list."""
    monkeypatch.setattr(pm.json, 'load', mock_called)
    pmng = pm.PluginManager()
    assert pmng.plugins == []
    assert not hasattr(mock_called, 'called')

def test_installed_pkgs_envdisabled(disabled):
    """Test plugin manager loading installed plugin list disabled by env var."""
    pmng = pm.PluginManager()
    assert pmng.installed_pkgs == {}
    assert pmng._installed is None

def test_installed_file_mock(monkeypatch, mock_installed_file, mock_called):
    """Test plugin manager loading installed pkgs list."""
    pmng = pm.PluginManager()
    assert isinstance(pmng.installed_pkgs, dict)
    assert pmng._installed is not None
    assert pmng.installed_pkgs == mock_installed_file

    # Test caching of file
    monkeypatch.setattr(pm.json, 'load', mock_called)
    pmng.installed_pkgs  # pylint: disable=pointless-statement
    assert not hasattr(mock_called, 'called')

def test_save_plugin_list_disabled(monkeypatch, disabled, mock_called):
    """Test plugin manager saving installed plugin list with disabled plugins."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm.json, 'dump', mock_called)
    pmng.save_plugin_list()
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

def test_save_installed_disabled(monkeypatch, disabled, mock_called):
    """Test plugin manager saving installed pkgs list with disabled plugins."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm.json, 'dump', mock_called)
    pmng.save_installed()
    assert not hasattr(mock_called, 'called')

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

def test_install_plugin_thread_lock(monkeypatch, mock_plugin_data):
    """Test plugin manager installing a plugin with thread lock."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pmng, '_install_plugin', lambda *a: time.sleep(0.25))
    name = mock_plugin_data[0]['name']

    ran = [1,0,0,0,0]
    def install(i):
        nonlocal ran
        pmng.install_plugin(name)
        ran[i+1] = 1
        assert ran[i] == 1

    threads = []
    for i in range(4):
        t = threading.Thread(target=install, args=(i,))
        t.start()
        time.sleep(0.005)
        threads.append(t)

    for t in threads:
        t.join()

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

def test_uninstall_plugin_thread_lock(monkeypatch, mock_plugin_data, mock_called):
    """Test plugin manager removing a plugin with thread lock."""
    name = mock_plugin_data[0]['name']
    pkg = mock_plugin_data[0]['package']

    pmng = pm.PluginManager()
    monkeypatch.setattr(pmng, '_plugins', [name])
    monkeypatch.setattr(pm.settings, 'INSTALLED_APPS', [name])
    monkeypatch.setattr(pmng, '_plugins', [name])
    monkeypatch.setattr(pmng, '_installed', {f'{pm.GENERIC_SCOPE}::{pkg}' : {}})
    monkeypatch.setattr(pmng, 'uninstall_package', lambda x: time.sleep(0.25))

    ran = [1,0,0,0,0]
    def uninstall(i):
        nonlocal ran
        pmng.uninstall_plugin(name)
        ran[i+1] = 1
        assert ran[i] == 1

    threads = []
    for i in range(4):
        t = threading.Thread(target=uninstall, args=(i,))
        t.start()
        if i == 1:
            monkeypatch.setattr(pmng, 'get_plugin_data', mock_called)
        time.sleep(0.005)
        threads.append(t)

    for t in threads:
        t.join()

    assert name not in pmng.plugins
    assert not hasattr(mock_called, 'called')

def test_install_package_unkown_scope(monkeypatch, mock_called):
    """Test plugin manager installing a package with unknown scope."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    scope = 'unknown'
    pmng.install_package(name, version, scope=scope)
    assert not hasattr(mock_called, 'called')

def test_find_site_packages_none():
    """Test plugin manager finding site packages not existing."""
    pmng = pm.PluginManager()
    # sp_dir = pmng.plugin_dir / 'test123' / 'site-packages'
    assert pm.find_site_packages(pmng.plugin_dir) is None

def test_find_site_packages_exists():
    """Test plugin manager finding site packages existing."""
    pmng = pm.PluginManager()
    sp_dir = pmng.plugin_dir / 'test123' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    assert pm.find_site_packages(pmng.plugin_dir) == sp_dir

def test_install_package_unkown_system(monkeypatch, mock_called):
    """Test plugin manager installing a package with unknown system."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    system = 'unknown'
    pmng.install_package(name, version, system=system)
    assert not hasattr(mock_called, 'called')

def test_install_package_nospdir(monkeypatch, mock_called):
    """Test plugin manager installing a package without any file created."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    scope = pm.GENERIC_SCOPE
    with pytest.raises(FileNotFoundError):
        pmng.install_package(name, version, scope=scope)

def test_install_package_install_file_dirs(monkeypatch, mock_called):
    """Test plugin manager installing a package with file created."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    scope = pm.GENERIC_SCOPE
    scoped_name = f'{scope}::{name}'
    filename = 'test_file'
    dirname = 'test_dir'

    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    (sp_dir / filename).touch()
    (sp_dir / dirname).mkdir()
    (sp_dir / '__pycache__').mkdir()  # Test that __pycache__ is ignored

    pmng.install_package(name, version, scope=scope)
    assert hasattr(mock_called, 'called')
    assert scoped_name in pmng.installed_pkgs

    assert (pmng.PLUGIN_SP[scope] / filename).exists()
    assert (pmng.PLUGIN_SP[scope] / dirname).exists()
    assert pmng.installed_pkgs[scoped_name]['files'] == [filename]
    assert pmng.installed_pkgs[scoped_name]['dirs'] == [dirname]


def test_install_package_install_file_overwrite(monkeypatch, mock_called):
    """Test plugin manager installing a package with overwriting existing file."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    scope = pm.GENERIC_SCOPE
    scoped_name = f'{scope}::{name}'
    filename = 'test_file'
    dst_file = pmng.PLUGIN_SP[scope] / filename

    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    with (sp_dir / 'test_file').open('w') as f:
        f.write('test_new')
    with dst_file.open('w') as f:
        f.write('test_old')

    pmng.install_package(name, version, scope=scope)
    assert hasattr(mock_called, 'called')
    assert scoped_name in pmng.installed_pkgs

    assert dst_file.exists()
    assert dst_file.read_text() == 'test_new'
    assert pmng.installed_pkgs[scoped_name]['files'] == [filename]


def test_install_package_install_dir_merge(monkeypatch, mock_called):
    """Test plugin manager installing a package with dir merging."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    scope = pm.GENERIC_SCOPE
    scoped_name = f'{scope}::{name}'
    dirname = 'test_dir'
    file_old = 'test_file_old'
    file_new = 'test_file_new'

    dst = pmng.PLUGIN_SP[scope]

    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    (sp_dir / dirname).mkdir(parents=True, exist_ok=True)
    (dst / dirname).mkdir(parents=True, exist_ok=True)
    (sp_dir / dirname / file_old).touch()
    (dst / dirname / file_new).touch()

    pmng.install_package(name, version, scope=scope)
    assert hasattr(mock_called, 'called')
    assert scoped_name in pmng.installed_pkgs

    assert (dst / dirname / file_old).exists()
    assert (dst / dirname / file_new).exists()

def test_install_package_install_twice(monkeypatch, mock_called):
    """Test plugin manager installing an already installed package."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    scope = pm.GENERIC_SCOPE
    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    pmng.install_package(name, version, scope=scope)
    assert mock_called.called
    assert f'{scope}::{name}' in pmng.installed_pkgs

    # Test that on second call the install action is skipped
    del mock_called.called
    pmng.install_package(name, version, scope=scope)
    assert not hasattr(mock_called, 'called')

def test_install_package_overwrite_version(monkeypatch, mock_called):
    """Test plugin manager installing an already installed package with different version."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    scope = pm.GENERIC_SCOPE
    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    pmng.install_package(name, version, scope=scope)
    assert mock_called.called
    assert f'{scope}::{name}' in pmng.installed_pkgs

    # Test that installing different version triggers the install action and removes the old version
    version = '2.0'
    del mock_called.called
    sp_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(pmng, '_uninstall_package', mock_called)
    pmng.install_package(name, version, scope=scope)
    assert  mock_called.called

def test_install_package_list_extras(monkeypatch, mock_called):
    """Test plugin manager installing with `list` extras."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    extras = ['extra1', 'extra2']
    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    pmng.install_package(name, version, extras=extras)
    assert mock_called.called
    assert mock_called.args[2] == extras

def test_install_package_str_extras(monkeypatch, mock_called):
    """Test plugin manager installing with `str` extras."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    extras = 'extra1 extra2'
    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    pmng.install_package(name, version, extras=extras)
    assert mock_called.called
    assert mock_called.args[2] == extras.split(' ')

def test_install_package_env_override_version(monkeypatch, mock_called):
    """Test plugin manager installing overriding using envvar: version."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    override_version = '2.0'

    monkeypatch.setenv(f'OCT_PKG_{pm.get_safe_name(name).upper()}_VERSION', override_version)

    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    pmng.install_package(name, version)

    assert mock_called.called
    assert mock_called.args[0] == f'{name}=={override_version}'

def test_install_package_env_override_extras(monkeypatch, mock_called):
    """Test plugin manager installing overriding using envvar: extras."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    override_extras = 'abc 123'

    monkeypatch.setenv(f'OCT_PKG_{pm.get_safe_name(name).upper()}_EXTRAS', override_extras)

    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    pmng.install_package(name, version)

    assert mock_called.called
    assert mock_called.args[2] == override_extras.split(' ')

def test_install_package_env_override_scope(monkeypatch, device, mock_called):
    """Test plugin manager installing overriding using envvar: scope."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pm, '_pip_install', mock_called)
    name = 'test'
    version = '1.0'
    override_scope = device

    monkeypatch.setenv(f'OCT_PKG_{pm.get_safe_name(name).upper()}_SCOPE', override_scope)

    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)
    pmng.install_package(name, version, scope=pm.GENERIC_SCOPE)

    assert mock_called.called
    assert f'{override_scope}::{name}' in pmng.installed_pkgs

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

def test_uninstall_package_different_scope(monkeypatch, mock_called):
    """Test plugin manager uninstalling a package ."""
    scope = 'random_scope'
    name = f'{scope}::pkg4'
    pmng = pm.PluginManager()

    pmng._installed = {}
    pmng._installed[name] = {}
    monkeypatch.setattr(pmng, 'save_installed', mock_called)

    pmng.uninstall_package(name)
    assert not hasattr(mock_called, 'called')
    assert name in pmng.installed_pkgs

def test_install_package_thread_lock(monkeypatch):
    """Test plugin manager installing a package with thread lock."""
    monkeypatch.setattr(pm, '_pip_install', lambda *a: time.sleep(0.25))

    pmng = pm.PluginManager()
    name = 'test'
    version = '1.0'
    scope = pm.GENERIC_SCOPE
    sp_dir = pmng.plugin_dir / 'test' / 'site-packages'
    sp_dir.mkdir(parents=True, exist_ok=True)

    ran = [1,0,0,0,0]
    def install(i):
        nonlocal ran
        pmng.install_package(name, version, scope=scope)
        ran[i+1] = 1
        assert ran[i] == 1

    threads = []
    for i in range(4):
        t = threading.Thread(target=install, args=(i,))
        t.start()
        time.sleep(0.005)
        threads.append(t)

    for t in threads:
        t.join()

def test_uninstall_package_thread_lock(monkeypatch, mock_installed_file):
    """Test plugin manager uninstalling a package with thread lock."""
    class MockDict(dict):
        called = False
        def pop(self, *args):
            MockDict.called = True
            time.sleep(0.25)

    scope = pm.GENERIC_SCOPE
    name = f'{scope}::pkg4'
    pmng = pm.PluginManager()

    ran = [1,0,0,0,0]
    def uninstall(i):
        nonlocal ran
        pmng.uninstall_package(f'{scope}::{name}')
        ran[i+1] = 1
        assert ran[i] == 1

    threads = []
    for i in range(4):
        t = threading.Thread(target=uninstall, args=(i,))
        t.start()
        if i == 1:
            monkeypatch.setattr(pmng, '_installed', MockDict())
        time.sleep(0.005)
        threads.append(t)

    for t in threads:
        t.join()
    assert name not in pmng.installed_pkgs
    assert not MockDict.called

def test_ensure_plugins(monkeypatch, mock_called, tmp_base_dir, mock_plugin_file, mock_plugin_data):
    """Test initializer ensure plugins."""
    pmng = pm.PluginManager()
    monkeypatch.setattr(pmng, 'install_plugin', mock_called)
    ini.ensure_plugins()
    assert mock_called.called
