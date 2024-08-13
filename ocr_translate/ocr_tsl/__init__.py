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
"""Initialize the server based on environment variables."""

import os
from typing import Callable

from django.db.utils import OperationalError

from .initializers import auto_create_languages, init_most_used

FAIL = False

def run_on_env(env_name: str, func: Callable):
    """Run a function if the environment variable is set."""
    global FAIL
    if os.environ.get(env_name, 'false').lower() == 'true':
        try:
            func()
            print(f'INFO: Ran `{func.__name__}` based on environment variable `{env_name}`')
        except OperationalError as exc:
            FAIL = True
            print(f'WARNING: Ignoring environment variable `{env_name}` as the database is not ready/migrated.')
            print(f'WARNING: {exc}')

run_on_env('AUTOCREATE_LANGUAGES', auto_create_languages)
run_on_env('LOAD_ON_START', init_most_used)

if FAIL:
    print('WARNING: Create/migrate the database by running `python manage.py migrate`')
