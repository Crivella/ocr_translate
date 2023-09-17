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

from .initializers import (auto_create_languages, auto_create_models,
                           init_most_used)

if os.environ.get('AUTOCREATE_LANGUAGES', 'false').lower() == 'true':
    auto_create_languages()

if os.environ.get('AUTOCREATE_VALIDATED_MODELS', 'false').lower() == 'true':
    auto_create_models()

if os.environ.get('LOAD_ON_START', 'false').lower() == 'true':
    init_most_used()
