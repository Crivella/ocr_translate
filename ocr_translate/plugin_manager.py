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

# pylint: disable=redefined-outer-name,unspecified-encoding,too-many-branches

import json
import logging
import os
import shutil
import site
import subprocess
import sys
from importlib import resources
from pathlib import Path

from django.apps import apps
from django.conf import settings

GENERIC_SCOPE = 'generic'
DEVICE = os.environ.get('DEVICE', 'cpu')
SCOPES = [GENERIC_SCOPE, DEVICE]

OCT_BASE_DIR: Path = Path(os.environ.get('OCT_BASE_DIR', Path.home() / '.ocr_translate'))
PLUGIN_DIR: Path = OCT_BASE_DIR / 'plugins'
PLUGIN_SP: dict[str, Path] = {}

for scope in SCOPES:
    d = PLUGIN_DIR / scope
    d.mkdir(exist_ok=True, parents=True)
    PLUGIN_SP[scope] = d
    if scope in SCOPES:
        sys.path.insert(0, d.as_posix())
sys.path_importer_cache.clear()

site.USER_BASE = PLUGIN_DIR.as_posix()
site.USER_SITE = PLUGIN_SP[GENERIC_SCOPE].as_posix()

PLUGIN_LIST_FILE: Path = OCT_BASE_DIR / 'plugins.json'
INSTALLED_FILE: Path = PLUGIN_DIR / 'installed.json'

INSTALLED: dict[str, dict] = {}
if INSTALLED_FILE.exists():
    with open(INSTALLED_FILE) as f:
        INSTALLED = json.load(f)
DONE: dict[str, str] = {}

PLUGINS: list[str] = []
if not os.environ.get('OCT_DISABLE_PLUGINS', False):
    if PLUGIN_LIST_FILE.exists():
        with open(PLUGIN_LIST_FILE) as f:
            PLUGINS = json.load(f)

logger = logging.getLogger('ocr.general')

# sys.OpenCV_LOADER_DEBUG = True
# print('PLUGIN_SP:', PLUGIN_SP)
# print('OS.NAME:', os.name)
# subprocess.run(['pip', 'show', 'pip'], check=True)


def find_site_packages(start_dir: Path) -> Path:
    """Find the site-packages directory."""
    for pth in start_dir.rglob('site-packages'):
        return pth
    return None

def save_plugin_list():
    """Save the list of installed plugins."""
    with open(PLUGIN_LIST_FILE, 'w') as f:
        json.dump(PLUGINS, f, indent=2)


def save_installed():
    """Save the installed packages."""
    with open(INSTALLED_FILE, 'w') as f:
        json.dump(INSTALLED, f, indent=2)

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
        if INSTALLED[name]['version'] == vstring:
            return

    ptr = {}
    INSTALLED[name] = ptr
    ptr['version'] = vstring
    ptr['files'] = []
    ptr['dirs'] = []

    # print(f'  Installing {name}=={version}')
    logger.info(f'Installing {name}=={version}')
    cmd = [
        'pip', 'install', f'{name}=={version}',
        '--ignore-installed',
        '--no-deps',
        '--no-build-isolation',
        f'--prefix={PLUGIN_DIR}',
        ]
    if extras:
        cmd += extras.split(' ')
    res = subprocess.run(cmd, check=True, capture_output=True)
    logger.debug(res.stdout.decode())

    tmp_dir = find_site_packages(PLUGIN_DIR)
    print(tmp_dir)
    for pth in tmp_dir.iterdir():
        if pth.name.endswith('__pycache__'):
            continue
        # shutil.move(d, PLUGIN_SP[scope])
        dst = PLUGIN_SP[scope] / pth.name
        if pth.is_file():
            ptr['files'].append(pth.name)
            if dst.exists():
                dst.unlink()
            shutil.move(pth, dst)
        elif pth.is_dir():
            ptr['dirs'].append(pth.name)
            if dst.exists():
                shutil.copytree(pth, PLUGIN_SP[scope] / pth.name, dirs_exist_ok=True)
                shutil.rmtree(pth)
            else:
                shutil.move(pth, PLUGIN_SP[scope])
        else:
            raise ValueError(f'Unknown type: {pth}')

    save_installed()

def get_all_plugin_data() -> list[dict]:
    """Get the plugin data."""
    data_file = resources.files('ocr_translate') / 'plugins_data.json'
    if not data_file.exists():
        return []
    with open(data_file) as f:
        data = json.load(f)
    return data

def get_plugin_data(name: str) -> dict:
    """Get the data for a specific plugin."""
    data = get_all_plugin_data()
    for plugin in data:
        if plugin['name'] == name:
            return plugin
    return {}

def reload_plugins():
    """Reload the plugins."""
    apps.app_configs = {}
    apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
    apps.clear_cache()
    apps.populate(settings.INSTALLED_APPS)

def install_plugin(name):
    """Ensure the plugin is installed."""
    if name in PLUGINS:
        return
    data = get_all_plugin_data()
    for plugin in data:
        if plugin['name'] == name:
            break
    else:
        raise ValueError(f'Plugin {name} not found')
    data = plugin
    pkg = data['package']
    version = data['version']
    # description = data['description']
    deps = data.get('dependencies', [])

    logger.info(f'Installing plugin {pkg}=={version} with dependencies')
    for dep in deps[::-1]:
        pip_install(**dep)

    pip_install(pkg, version)

    PLUGINS.append(name)
    save_plugin_list()
    settings.INSTALLED_APPS.append(name)
    reload_plugins()

def uninstall_package(name):
    """Uninstall a package."""
    if name not in INSTALLED:
        return
    logger.info(f'Uninstalling package {name}')
    ptr = INSTALLED.pop(name)
    _, scope = ptr['version'].split('+')
    for f in ptr['files']:
        (PLUGIN_SP[scope] / f).unlink()
    for pth in ptr['pthirs']:
        shutil.rmtree(PLUGIN_SP[scope] / pth)

    save_installed()

    # version, scope = INSTALLED.pop(name).split('+')
    # with open(INSTALLED_FILE, 'w') as f:
    #     json.dump(INSTALLED, f, indent=2)

def uninstall_plugin(name):
    """Uninstall the plugin."""
    if name not in PLUGINS:
        return
    data = get_plugin_data(name)
    pkg = data['package']
    logger.info(f'Uninstalling plugin {name} and non-shared dependencies')
    # logger.debug(f'INSTALLED: {INSTALLED}')
    if pkg not in INSTALLED:
        return

    data = get_all_plugin_data()
    other_deps = set()
    plugin_deps = set()
    torm_deps = set()
    for plugin in data:
        deps = set(_['name'] for _ in plugin.get('dependencies', []))
        if plugin['name'] == name:
            plugin_deps |= deps
        else:
            other_deps |= deps
    torm_deps = plugin_deps - other_deps

    for dep in torm_deps:
        uninstall_package(dep)

    PLUGINS.remove(name)
    save_plugin_list()

    settings.INSTALLED_APPS.remove(name)
    reload_plugins()
