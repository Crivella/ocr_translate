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
# pylint: disable=import-outside-toplevel

import os
from pathlib import Path

import django
import torch
from django.core.management import call_command


def main():
    """Run the django migrations and start the server."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    home = Path.home()
    if not 'TRANSFORMERS_CACHE' in os.environ:
        os.environ['TRANSFORMERS_CACHE'] = str(home / '.ocr_translate')
        home.mkdir(exist_ok=True, parents=True)
    if not 'DATABASE_NAME' in os.environ:
        os.environ['DATABASE_NAME'] = str(home / '.ocr_translate' / 'db.sqlite3')
        home.mkdir(exist_ok=True, parents=True)

    if not torch.cuda.is_available():
        print('CUDA is not available, falling back to using CPU')
        os.environ['DEVICE'] = 'cpu'
    else:
        os.environ.setdefault('DEVICE', 'cuda')

    django.setup()

    from ocr_translate.ocr_tsl.initializers import (auto_create_languages,
                                                    auto_create_models,
                                                    init_most_used)

    call_command('migrate')

    auto_create_languages()
    auto_create_models()
    init_most_used()

    call_command('runserver', '--noreload', '4000')

if __name__ == '__main__':
    main()
