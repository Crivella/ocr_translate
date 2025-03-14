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
"""Run the django migrations and start the server."""
# pylint: disable=import-outside-toplevel,too-many-statements,invalid-name,wrong-import-position

import importlib
import os
import subprocess
import sys
from pathlib import Path

req_version = os.environ.get('OCT_VERSION', '0.6.2').lower()

def install_upgrade(upgrade=False):
    """Install or upgrade the ocr_translate package."""
    cmd = ['pip', 'install']
    if upgrade:
        print(f'Upgrading ocr_translate to {req_version}...')
        cmd.append('--upgrade')
    else:
        print(f'Installing ocr_translate {req_version}...')
    if req_version in ['latest', 'last']:
        cmd.append('django-ocr_translate')
    else:
        cmd.append(f'django-ocr_translate=={req_version}')
    subprocess.run(cmd, check=True)
    print('...done')

if os.environ.get('OCT_AUTOUPDATE', 'false').lower() in ['true', 't', '1']:
    install_upgrade(upgrade=True)

try:
    import django
except ImportError:
    print('Django not found: installing django-ocr_translate...')
    install_upgrade()
    import django

from django.core.management import call_command

import ocr_translate.plugin_manager as pm
from ocr_translate import __version__

if __version__ != req_version:
    print(f'Warning: version mismatch, expected OCT_VERSION={req_version} but found {__version__}')
    print('  If you are using a new release with a previously existing virtual environment,')
    print('  please run the server with OCT_AUTOUPDATE set to "true" to update the environment.')
    print('  Alternatively set OCT_VERSION to the desired version to run the server with that version.')
    sys.exit(1)

def banner():
    """Print the banner."""
    print('--------------------------------------------')
    print('-                                          -')
    print(f'-     OCR_TRANSLATE version v{__version__:<13s} -')
    print('-                                          -')
    print('--------------------------------------------')

def env_default():
    """Set default environment variables."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    os.environ.setdefault('DJANGO_DEBUG', 'True')
    os.environ.setdefault('DJANGO_LOG_LEVEL', 'INFO')

def dir_check():
    """Check if required directories exist and create them if needed."""
    if not 'OCT_BASE_DIR' in os.environ:
        base = Path.home()  / '.ocr_translate'
        print(f'OCT_BASE_DIR not set:  Using "{base}" as base dir for ocr_translate')
        os.environ['OCT_BASE_DIR'] = base.as_posix()
    else:
        base = Path(os.environ['OCT_BASE_DIR'])
    base.mkdir(exist_ok=True, parents=True)

    if not 'DATABASE_NAME' in os.environ:
        print(f'DATABASE_NAME not set:  Using "{base / "db.sqlite3"}" as database')
        os.environ['DATABASE_NAME'] = (base / 'db.sqlite3').as_posix()
        base.mkdir(exist_ok=True, parents=True)
    elif (db_name := os.environ['DATABASE_NAME']).endswith('.sqlite3'):
        Path(db_name).parent.mkdir(exist_ok=True, parents=True)

def cuda_check():
    """Check if cuda is available and set the environment variable DEVICE."""
    print('Checking for CUDA availability...')
    if 'DEVICE' in os.environ:
        device = os.environ['DEVICE']
        print(f'Device set via environment variable to: `{device}`')
        if device == 'cpu':
            return
    else:
        try:
            subprocess.run(['nvidia-smi'], check=True, capture_output=True)
        except FileNotFoundError:
            pass
        else:
            print('`nvidia-smi` is available, setting DEVICE to `cuda`')
            os.environ['DEVICE'] = 'cuda'

    try:
        # The version of torch found depends on the current scope.
        # This check is still useful to se if a CUDA capable torch is installed but a GPU is not available.
        pm.PluginManager()  # Make sure the plugin manager is initialized to have installed plugins libs in path
        importlib.import_module('torch')
    except ModuleNotFoundError:
        print('Torch not found: cannot check for CUDA availability explicitly.')
        print('In case of errors try setting the DEVICE environment variable to "cpu"')
    else:
        print('Torch found, using it for CUDA availability check...')
        import torch
        if not torch.cuda.is_available():
            print('CUDA is not available, falling back to using CPU')
            os.environ['DEVICE'] = 'cpu'
        else:
            os.environ.setdefault('DEVICE', 'cuda')
            print('CUDA is available, using GPU')
        importlib.reload(pm)  # Reload the plugin manager to have the correct DEVICE set

def init():
    """Run server initializations"""
    from ocr_translate import models as m
    from ocr_translate.ocr_tsl.initializers import (auto_create_languages,
                                                    ensure_plugins)
    ac_lang = os.environ.get('AUTO_CREATE_LANGUAGES', 'false').lower() in ['true', '1']
    ac_lang |= m.Language.objects.count() == 0
    if ac_lang:
        print('Autocreate language entries in database...')
        auto_create_languages()
        os.environ['AUTO_CREATE_LANGUAGES'] = 'false'
    ensure_plugins()

def superuser():
    """Create a superuser if it does not exist and check for default password."""
    default_su_password = 'password'
    su_name = os.environ.get('DJANGO_SUPERUSER_USERNAME', '') or 'admin'
    su_pass = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '') or default_su_password
    if su_name and su_pass:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username=su_name).exists():
            print(f'Creating superuser "{su_name}" with password "{su_pass}"')
            User.objects.create_superuser(su_name, '', su_pass)
        else:
            print(f'Superuser "{su_name}" already exists')
            if User.objects.get(username=su_name).check_password(default_su_password):
                print(f'   password still set to the default "{default_su_password}"')

def main():
    """Run the django migrations and start the server."""
    banner()
    env_default()
    dir_check()
    print('--------------------------------------------')
    cuda_check()

    print('--------------------------------------------')
    print('Running django setup...')
    django.setup()

    print('Create database (if needed) and apply database migrations (if any)...')
    call_command('migrate')
    print('--------------------------------------------')

    superuser()
    print('--------------------------------------------')
    print('Running server initializations...')
    init()

    bind_address = os.environ.get('OCT_DJANGO_BIND_ADDRESS', '127.0.0.1')
    port = os.environ.get('OCT_DJANGO_PORT', '4000')

    print('--------------------------------------------')
    print('Starting server...')
    try:
        importlib.import_module('gunicorn')
    except ImportError:
        print('...using django development server')
        call_command('runserver', '--noreload', f'{bind_address}:{port}')
    else:
        print('...using gunicorn')
        import getpass
        user = os.environ.get('OCT_GUNICORN_USER', getpass.getuser())
        timeout = os.environ.get('OCT_GUNICORN_TIMEOUT', '1200')
        num_workers = os.environ.get('OCT_GUNICORN_NUM_WORKERS', '1')
        subprocess.run([
            'gunicorn', 'mysite.wsgi',
            '--user', user,
            '--bind', f'{bind_address}:{port}',
            '--timeout', timeout,
            '--workers', num_workers,
        ], check=True)

if __name__ == '__main__':
    main()
