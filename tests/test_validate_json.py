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
"""Check that the JSON files are valid."""

import json
from importlib import resources

MAIN_DEPS = set([
    'numpy',
    'Django',
    'Pillow',
    'opencv-python-headless'
])

def test_loadable():
    """Test that all json files are valide and loadable."""
    all_jsons = resources.files('ocr_translate').glob('**/*.json')
    for pth in all_jsons:
        with pth.open() as f:
            json.load(f)

def test_plugin_data_conflicts():
    """Test the absence of dependencies conflicts in `plugins_data.json`"""
    data_file = resources.files('ocr_translate') / 'plugins_data.json'
    with data_file.open() as f:
        data = json.load(f)

    done = {}
    for plugin in data:
        for dep in plugin.get('dependencies', []):
            name = dep['name']
            version = dep['version']
            scope = dep.get('scope', 'generic')
            key = (name, scope)
            assert name not in MAIN_DEPS, f'Dependency {name} should not be overriden'
            if key in done:
                assert done[key] == version, f'Conflict in {name} {scope} version: {done[key]} != {version}'
            else:
                done[key] = version
