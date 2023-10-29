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
# pylint: disable=import-outside-toplevel,too-many-statements,invalid-name

import importlib
import os
from pathlib import Path

import django
from django.core.management import call_command

from ocr_translate import __version__


def main():
    """Run the django migrations and start the server."""
    print('--------------------------------------------')
    print('-                                          -')
    print(f'-     OCR_TRANSLATE version v{__version__:<13s} -')
    print('-                                          -')
    print('--------------------------------------------')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    os.environ.setdefault('DJANGO_DEBUG', 'True')
    os.environ.setdefault('DJANGO_LOG_LEVEL', 'INFO')

    home = Path.home()  / '.ocr_translate'
    if not 'TRANSFORMERS_CACHE' in os.environ:
        print(f'TRANSFORMERS_CACHE not set:  Using "{home}" as transformers cache')
        os.environ['TRANSFORMERS_CACHE'] = str(home)
        home.mkdir(exist_ok=True, parents=True)
    if not 'DATABASE_NAME' in os.environ:
        print(f'DATABASE_NAME nto set:  Using "{home / "db.sqlite3"}" as database')
        os.environ['DATABASE_NAME'] = str(home / 'db.sqlite3')
        home.mkdir(exist_ok=True, parents=True)

    try:
        importlib.import_module('torch')
    except ModuleNotFoundError:
        pass
    else:
        import torch
        if not torch.cuda.is_available():
            print('CUDA is not available, falling back to using CPU')
            os.environ['DEVICE'] = 'cpu'
        else:
            print('CUDA is available, using GPU')
            os.environ.setdefault('DEVICE', 'cuda')

    print('Running django setup...')
    django.setup()

    from ocr_translate.ocr_tsl.initializers import (auto_create_languages,
                                                    auto_create_models,
                                                    init_most_used)

    print('Create database if needed and apply database migrations (if any)...')
    call_command('migrate')

    su_name = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    su_pass = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'password')
    if su_name and su_pass:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username=su_name).exists():
            print(f'Creating superuser "{su_name}" with password "{su_pass}"')
            User.objects.create_superuser(su_name, '', su_pass)


    ac_lang = os.environ.get('AUTO_CREATE_LANGUAGES', 'true')
    if ac_lang == 'true':
        print('Autocreate language entries in database...')
        auto_create_languages()
    ac_models = os.environ.get('AUTOCREATE_VALIDATED_MODELS', 'true')
    if ac_models == 'true':
        print('Autocreate validated models in database...')
        auto_create_models()
    if os.getenv('LOAD_ON_START', 'false') == 'true':
        print('Load most used models in memory...')
        init_most_used()

    print('Starting server...')
    call_command('runserver', '--noreload', '4000')

if __name__ == '__main__':
    main()
