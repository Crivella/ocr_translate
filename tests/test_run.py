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
"""Test run script utils."""
# pylint: disable=redefined-outer-name,missing-class-docstring,missing-function-docstring,invalid-name
import os

import pytest
from django.contrib.auth import get_user_model

from ocr_translate.ocr_tsl import initializers as ini
from ocr_translate.scripts import run

INIT_VARS = [
    'DJANGO_SETTINGS_MODULE', 'DJANGO_DEBUG', 'DJANGO_LOG_LEVEL',
]
OTHER_VARS = [
    'OCT_BASE_DIR', 'DATABASE_NAME',
    'DJANGO_SUPERUSER_USERNAME', 'DJANGO_SUPERUSER_PASSWORD',
]
ALL_VARS = INIT_VARS + OTHER_VARS


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables before each test."""
    old_env = {v: os.environ.get(v) for v in ALL_VARS}
    for v in ALL_VARS:
        if v in os.environ:
            del os.environ[v]
    yield
    for v, val in old_env.items():
        if val is not None:
            os.environ[v] = val
        elif v in os.environ:
            del os.environ[v]

@pytest.fixture(scope='function')
def oct_base_dir(tmp_path, monkeypatch):
    """Set the base directory to a temporary directory."""
    monkeypatch.setenv('OCT_BASE_DIR', str(tmp_path))
    return tmp_path

@pytest.fixture(scope='function')
def fake_home(tmp_path, monkeypatch):
    """Set the home directory to a temporary directory."""
    monkeypatch.setattr(run.Path, 'home', lambda: tmp_path)
    return tmp_path

@pytest.fixture(autouse=True)
def mock_ini_functions(monkeypatch):
    """Mock ini functions."""
    monkeypatch.setattr(ini, 'ensure_plugins', lambda *args, **kwargs: None)
    monkeypatch.setattr(ini, 'sync_models_epts', lambda *args, **kwargs: None)
    monkeypatch.setattr(ini, 'env_var_init', lambda *args, **kwargs: None)
    monkeypatch.setattr(ini, 'auto_create_languages', lambda *args, **kwargs: None)

def test_banner(capsys):
    """Test banner function."""
    run.banner()
    out = capsys.readouterr().out
    assert 'OCR_TRANSLATE version' in out
    assert f'v{run.__version__}' in out

def test_env_default_clean():
    """Test env_default function."""
    assert all(v not in os.environ for v in INIT_VARS)
    run.env_default()
    assert all(v in os.environ for v in INIT_VARS)

def test_env_default_override():
    """Test env_default function does not override existing vars."""
    os.environ['DJANGO_SETTINGS_MODULE'] = 'custom.settings'
    os.environ['DJANGO_DEBUG'] = 'ABC'
    os.environ['DJANGO_LOG_LEVEL'] = '123'
    run.env_default()
    assert os.environ['DJANGO_SETTINGS_MODULE'] == 'ocr_translate.app.settings'
    assert os.environ['DJANGO_DEBUG'] == 'ABC'
    assert os.environ['DJANGO_LOG_LEVEL'] == '123'

def test_dir_check(tmp_path):
    """Test dir_check function creates dirs if they do not exist."""
    base_dir = tmp_path / 'base_dir'
    db_dir = tmp_path / 'db_dir'
    os.environ['OCT_BASE_DIR'] = base_dir.as_posix()
    os.environ['DATABASE_NAME'] = (db_dir / 'db.sqlite3').as_posix()
    assert not base_dir.exists()
    assert not db_dir.exists()
    run.dir_check()
    assert base_dir.exists()
    assert db_dir.exists()

def test_dir_check_no_dbname(oct_base_dir):
    """Test dir_check function creates dirs if they do not exist."""
    assert 'DATABASE_NAME' not in os.environ
    run.dir_check()
    assert os.environ['DATABASE_NAME'] == (oct_base_dir / 'db.sqlite3').as_posix()

def test_dir_check_no_basedir(fake_home):
    """Test dir_check function creates dirs if they do not exist."""
    expected = fake_home / '.ocr_translate'

    assert 'OCT_BASE_DIR' not in os.environ
    run.dir_check()
    assert os.environ['OCT_BASE_DIR'] == expected.as_posix()
    assert expected.exists()

def test_cuda_check_env_cpu(monkeypatch, mock_called):
    """Test cuda_check function when nvidia-smi is not available."""
    monkeypatch.setenv('DEVICE', 'cpu')
    monkeypatch.setattr(run.importlib, 'import_module', mock_called)

    run.cuda_check()

    assert not hasattr(mock_called, 'called')

def test_cuda_check_env_invalid(monkeypatch, mock_called):
    """Test cuda_check function when nvidia-smi is not available."""
    monkeypatch.setenv('DEVICE', 'notvalid')
    monkeypatch.setattr(run.importlib, 'import_module', mock_called)

    run.cuda_check()

    assert not hasattr(mock_called, 'called')
    assert os.environ['DEVICE'] == 'cpu'

def test_cuda_check_env_notset_with_smi(monkeypatch, mock_called):
    """Test cuda_check function when nvidia-smi is not available."""
    def mock_raises(*args, **kwargs):
        mock_called(*args, **kwargs)
    def mock_import_error(name):
        raise ImportError
    class MockPluginManager:
        plugin_dir = None
        plugin_list_file = None
    monkeypatch.delenv('DEVICE', raising=False)
    monkeypatch.setattr(run.subprocess, 'run', mock_raises)
    monkeypatch.setattr(run.pm, 'PluginManager', lambda: MockPluginManager)
    monkeypatch.setattr(run.importlib, 'import_module', mock_import_error)

    run.cuda_check()

    assert hasattr(mock_called, 'called')
    assert mock_called.args[0] == ['nvidia-smi']
    assert os.environ['DEVICE'] == 'cuda'

def test_cuda_check_env_notset_without_smi(monkeypatch, mock_called):
    """Test cuda_check function when nvidia-smi is not available."""
    def mock_raises(*args, **kwargs):
        mock_called(*args, **kwargs)
        raise FileNotFoundError
    def mock_module_notfound(name):
        raise ModuleNotFoundError
    monkeypatch.delenv('DEVICE', raising=False)
    monkeypatch.setattr(run.subprocess, 'run', mock_raises)
    monkeypatch.setattr(run.pm, 'PluginManager', lambda: None)
    monkeypatch.setattr(run.importlib, 'import_module', mock_module_notfound)

    run.cuda_check()

    assert hasattr(mock_called, 'called')
    assert mock_called.args[0] == ['nvidia-smi']
    assert os.environ['DEVICE'] == 'cpu'

def test_cuda_check_env_failcheck_modulenotfound(monkeypatch, mock_called):
    """Test cuda_check function when nvidia-smi is not available."""
    def mock_module_notfound(*args, **kwargs):
        mock_called(*args, **kwargs)
        raise ModuleNotFoundError
    monkeypatch.setenv('DEVICE', 'cuda')
    monkeypatch.setattr(run.pm, 'PluginManager', lambda: None)
    monkeypatch.setattr(run.importlib, 'import_module', mock_module_notfound)

    run.cuda_check()

    assert hasattr(mock_called, 'called')
    assert mock_called.args[0] == 'torch'
    assert os.environ['DEVICE'] == 'cpu'

def test_cuda_check_env_cuda_not_vailable(monkeypatch):
    """Test cuda_check function when nvidia-smi is not available."""
    class MockTorch:
        __path__ = ['mocked_path']
        @property
        def cuda(self):
            return self
        def is_available(self):
            return False

    monkeypatch.setenv('DEVICE', 'cuda')
    monkeypatch.setattr(run.pm, 'PluginManager', lambda: None)
    monkeypatch.setattr(run.importlib, 'import_module', lambda *args: MockTorch())

    run.cuda_check()

    assert os.environ['DEVICE'] == 'cpu'

def test_cuda_check_env_cuda_vailable(monkeypatch):
    """Test cuda_check function when nvidia-smi is not available."""
    class MockTorch:
        __path__ = ['mocked_path']
        @property
        def cuda(self):
            return self
        def is_available(self):
            return True

    monkeypatch.setenv('DEVICE', 'cuda')
    monkeypatch.setattr(run.pm, 'PluginManager', lambda: None)
    monkeypatch.setattr(run.importlib, 'import_module', lambda *args: MockTorch())

    run.cuda_check()

    assert os.environ['DEVICE'] == 'cuda'

@pytest.mark.django_db
def test_superuser_defaults(capsys):
    """Test superuser creation with default credentials."""
    su_name = 'admin'
    default_su_password = 'password'
    User = get_user_model()
    assert User.objects.count() == 0
    run.superuser()
    assert User.objects.count() == 1
    assert User.objects.get(username=su_name).check_password(default_su_password)

    capsys.readouterr()
    # Run again with default password and see that warning is correctly printed
    run.superuser()
    out = capsys.readouterr().out
    assert 'password still set to the default' in out


@pytest.mark.django_db
def test_superuser_new():
    """Test superuser creation with default credentials."""
    su_name = 'admin'
    default_su_password = 'password'
    User = get_user_model()
    assert User.objects.count() == 0
    run.superuser()
    assert User.objects.count() == 1
    assert User.objects.get(username=su_name).check_password(default_su_password)

    new_name = 'newadmin'
    new_pass = 'newpassword'
    os.environ['DJANGO_SUPERUSER_USERNAME'] = new_name
    os.environ['DJANGO_SUPERUSER_PASSWORD'] = new_pass
    run.superuser()
    assert User.objects.count() == 2
    assert User.objects.get(username=new_name).check_password(new_pass)

@pytest.mark.django_db
def test_init_no_languages(monkeypatch, mock_called):
    """Test init function when no languages are present."""
    monkeypatch.setattr(ini, 'auto_create_languages', mock_called)
    run.init()
    assert hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_init_with_languages(monkeypatch, mock_called, language):
    """Test init function when no languages are present."""
    monkeypatch.setattr(ini, 'auto_create_languages', mock_called)
    run.init()
    assert not hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_start_with_gunicorn(monkeypatch, mock_called):
    """Test main function with gunicorn."""
    def mock_import(name):
        if name == 'gunicorn':
            return True
        raise ImportError
    monkeypatch.setattr(run.importlib, 'import_module', mock_import)
    monkeypatch.setattr(run.subprocess, 'run', mock_called)

    bind_addr = 'abc.def.ghi.jkl'
    port = '1234'
    monkeypatch.setenv('OCT_DJANGO_BIND_ADDRESS', bind_addr)
    monkeypatch.setenv('OCT_DJANGO_PORT', port)

    assert not hasattr(mock_called, 'called')
    run.start()
    assert hasattr(mock_called, 'called')

    launch_str = ' '.join(mock_called.args[0])
    assert 'gunicorn' in launch_str
    assert f'--bind {bind_addr}:{port}' in launch_str

@pytest.mark.django_db
def test_start_with_developserver(monkeypatch, mock_called):
    """Test main function with gunicorn."""
    def mock_import(name):
        raise ImportError
    monkeypatch.setattr(run.importlib, 'import_module', mock_import)
    monkeypatch.setattr(run, 'call_command', mock_called)

    bind_addr = 'abc.def.ghi.jkl'
    port = '1234'
    monkeypatch.setenv('OCT_DJANGO_BIND_ADDRESS', bind_addr)
    monkeypatch.setenv('OCT_DJANGO_PORT', port)

    assert not hasattr(mock_called, 'called')
    run.start()
    assert hasattr(mock_called, 'called')

    launch_str = ' '.join(mock_called.args)
    assert 'runserver' in launch_str
    assert f'{bind_addr}:{port}' in launch_str
