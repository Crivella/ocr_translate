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

import importlib
import json
import os
import site
import subprocess
import sys
from importlib import resources
from pathlib import Path

python_version = f'{sys.version_info.major}.{sys.version_info.minor}'

OCT_BASE_DIR = Path(os.environ.get('OCT_BASE_DIR', Path.home() / '.ocr_translate'))
PLUGIN_DIR = OCT_BASE_DIR / 'plugins'
PLUGIN_SP = PLUGIN_DIR / 'lib' / f'python{python_version}' / 'site-packages'
PLUGIN_SP.mkdir(exist_ok=True, parents=True)

sys.path.insert(0, PLUGIN_SP.as_posix())
sys.path_importer_cache.clear()

site.USER_BASE = PLUGIN_DIR.as_posix()
site.USER_SITE = PLUGIN_SP.as_posix()

INSTALLED_FILE = PLUGIN_DIR / 'installed.json'

INSTALLED = {}
if INSTALLED_FILE.exists():
    with open(INSTALLED_FILE) as f:
        INSTALLED = json.load(f)
DONE = {}

def pip_install(package, version, exras='', force=False):
    """Use pip to install a package."""
    if package in INSTALLED:
        if INSTALLED[package] == version:
            return
    if package in DONE:
        if DONE[package] == version:
            return
        raise ValueError(f'Coneflict: {package}=={version} already installed as {DONE[package]}')
    print(f'  Installing {package}=={version}')
    cmd = [
        'pip', 'install', f'{package}=={version}',
        '--ignore-installed',
        '--no-deps', '--no-build-isolation',
        f'--prefix={PLUGIN_DIR}',
        ]
    if exras:
        cmd += exras.split(' ')
    subprocess.run(cmd, check=True, capture_output=True)
    INSTALLED[package] = version
    DONE[package] = version
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
    plugin_file = OCT_BASE_DIR / 'plugins.json'
    if plugin_file.exists():
        with open(plugin_file) as f:
            plugins = json.load(f)

    for plugin in plugins:
        install_plugin(plugin)
    return plugins

def install_plugin(name, force=False):
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

    try:
        importlib.import_module(pkg)
        if not force:
            return
    except ImportError:
        pass

    for dep in deps[::-1]:
        dep, extras = (dep.split(';') + [''])[:2]
        dep_name, dep_version = dep.split('==')
        pip_install(dep_name, dep_version, extras)

    pip_install(pkg, version)
