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

from .initializers import auto_create_languages, init_last_used, init_most_used

FAIL = False

def run_on_env(env_name: str, func_map: dict[str, Callable], value: str = 'true'):
    """Run a function if the environment variable is set."""
    global FAIL
    if env_name in os.environ:
        value = os.environ.get(env_name).lower()
        if value in func_map:
            try:
                func = func_map[value]
                func()
                print(f'INFO: Ran `{func.__name__}` based on environment variable `{env_name}`')
            except OperationalError as exc:
                FAIL = True
                print(f'WARNING: Ignoring environment variable `{env_name}` as the database is not ready/migrated.')
                print(f'WARNING: {exc}')
        else:
            print('Unknown value for environment variable `{env_name}`: {value}')

def deprecate_los_true():
    """Deprecate the environment variable `LOAD_ON_START=true`."""
    print('WARNING: The environment variable `LOAD_ON_START=true` is deprecated (defaults to `most`).')
    print('WARNING: Use `LOAD_ON_START=most` or `LOAD_ON_START=last` instead.')
    init_most_used()

run_on_env(
    'AUTOCREATE_LANGUAGES',
    {
        'true': auto_create_languages,
        'false': lambda: None
    }
)
run_on_env(
    'LOAD_ON_START',
    {
        'most': init_most_used,
        'last': init_last_used,
        'true': deprecate_los_true,
        'false': lambda: None
    }
)

if FAIL:
    print('WARNING: Create/migrate the database by running `python manage.py migrate`')
