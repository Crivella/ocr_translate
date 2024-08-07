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
"""Utils to manage ocr_translate plugins."""

import json
import os
import site
import subprocess
import sys
from importlib import resources
from pathlib import Path

python_version = f'{sys.version_info.major}.{sys.version_info.minor}'

GENERIC_SCOPE = 'generic'
DEVICE = os.environ.get('DEVICE', 'cpu')
SCOPES = [GENERIC_SCOPE, DEVICE]

OCT_BASE_DIR = Path(os.environ.get('OCT_BASE_DIR', Path.home() / '.ocr_translate'))
PLUGIN_DIR = OCT_BASE_DIR / 'plugins'
PLUGIN_SP = {}

for scope in SCOPES:
    d = PLUGIN_DIR / scope
    d.mkdir(exist_ok=True, parents=True)
    PLUGIN_SP[scope] = d
    if scope in SCOPES:
        sys.path.insert(0, d.as_posix())
sys.path_importer_cache.clear()

site.USER_BASE = PLUGIN_DIR.as_posix()
site.USER_SITE = PLUGIN_SP[GENERIC_SCOPE].as_posix()

PLUGIN_LIST_FILE = OCT_BASE_DIR / 'plugins.json'
INSTALLED_FILE = PLUGIN_DIR / 'installed.json'

INSTALLED = {}
if INSTALLED_FILE.exists():
    with open(INSTALLED_FILE) as f:
        INSTALLED = json.load(f)
DONE = {}

print('OS.NAME:', os.name)
subprocess.run(['pip', 'show', 'pip'], check=True)


def pip_install(name, version, extras='', scope=GENERIC_SCOPE, force=False):
    """Use pip to install a package."""
    if scope not in SCOPES:
        return
    vstring = f'{version}+{scope}'
    if name in DONE:
        if DONE[name] == vstring:
            return
        raise ValueError(f'Coneflict: {name}=={version} already installed as {DONE[name]}')
    DONE[name] = vstring

    if not force and name in INSTALLED:
        if INSTALLED[name] == vstring:
            return
    INSTALLED[name] = vstring

    print(f'  Installing {name}=={version}')
    cmd = [
        'pip', 'install', f'{name}=={version}',
        '--ignore-installed',
        '--no-deps',
        # '--no-build-isolation',
        f'--target={PLUGIN_SP[scope]}',
        ]
    if extras:
        cmd += extras.split(' ')
    subprocess.run(cmd, check=True, capture_output=True)
    with open(INSTALLED_FILE, 'w') as f:
        json.dump(INSTALLED, f, indent=2)

def get_plugin_data() -> list[dict]:
    """Get the plugin data."""
    data_file = resources.files('ocr_translate') / 'plugins_data.json'
    if not data_file.exists():
        return []
    with open(data_file) as f:
        data = json.load(f)
    return data

def load_plugins_list() -> list[str]:
    """Get the list of available plugins."""
    plugins: list[str] = []
    if PLUGIN_LIST_FILE.exists():
        with open(PLUGIN_LIST_FILE) as f:
            plugins = json.load(f)

    for plugin in plugins:
        install_plugin(plugin)
    return plugins

def install_plugin(name):
    """Ensure the plugin is installed."""
    data = get_plugin_data()
    for plugin in data:
        if plugin['name'] == name:
            break
    else:
        raise ValueError(f'Plugin {name} not found')
    data = plugin
    pkg = data['package']
    version = data['version']
    description = data['description']
    deps = data.get('dependencies', [])

    for dep in deps[::-1]:
        pip_install(**dep)

    pip_install(pkg, version)
