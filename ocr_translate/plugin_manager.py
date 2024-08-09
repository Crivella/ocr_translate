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
DEFAULT_OCT_BASE_DIR: Path = Path.home() / '.ocr_translate'

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

def reload_django_apps():
    """Reload the plugins."""
    apps.app_configs = {}
    apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
    apps.clear_cache()
    apps.populate(settings.INSTALLED_APPS)

def _pip_install(package: str, prefix: str, extras: list[str] = None):
    """Install a package with pip."""
    if extras is None:
        extras = []
    logger.info(f'Installing {package}')
    cmd = [
        'pip', 'install', package,
        '--ignore-installed',
        '--no-deps',
        '--no-build-isolation',
        f'--prefix={prefix}',
        ] + extras
    res = subprocess.run(cmd, check=True, capture_output=True)
    logger.debug(res.stdout.decode())

class PluginManager:
    """Manage the plugins."""
    SINGLETON = None

    device: str = None
    scopes: list[str] = None

    base_dir: Path = None
    plugin_dir: Path = None
    PLUGIN_SP: dict[str, Path] = {}

    plugin_list_file: Path = None
    installed_file: Path = None

    @classmethod
    def get_manager(cls):
        """Return the singleton instance of the plugin manager."""
        if not PluginManager.SINGLETON:
            PluginManager.SINGLETON = PluginManager()
        return PluginManager.SINGLETON

    def __init__(self):
        """Initialize the plugin manager."""
        self.device = os.environ.get('DEVICE', 'cpu')
        self.scopes = [GENERIC_SCOPE, self.device]
        self.base_dir = Path(os.environ.get('OCT_BASE_DIR', DEFAULT_OCT_BASE_DIR))
        self.plugin_dir = self.base_dir / 'plugins'

        self.plugin_list_file = self.base_dir / 'plugins.json'
        self.installed_file = self.plugin_dir / 'installed.json'

        self._plugins = None
        self._plugin_data = None
        self._installed = None

        self.initialize_scopes()

    @property
    def plugins_data(self) -> list[dict]:
        """Get/cache the plugin data."""
        if self._plugin_data is None:
            data_file = resources.files('ocr_translate') / 'plugins_data.json'
            if not data_file.exists():
                self._plugin_data = []
            else:
                with open(data_file) as f:
                    self._plugin_data = json.load(f)
        return self._plugin_data

    def get_plugin_data(self, name: str) -> dict:
        """Get the data for a specific plugin."""
        for plugin in self.plugins_data:
            if plugin['name'] == name:
                return plugin
        return {}

    def initialize_scopes(self):
        """Configure the scopes."""
        for scope in self.scopes:
            pth = self.plugin_dir / scope
            pth.mkdir(exist_ok=True, parents=True)
            self.PLUGIN_SP[scope] = pth
            sys.path.insert(0, pth.as_posix())
        sys.path_importer_cache.clear()

        site.USER_BASE = self.plugin_dir.as_posix()
        site.USER_SITE = self.PLUGIN_SP[GENERIC_SCOPE].as_posix()

    @property
    def plugins(self) -> list[str]:
        """Get/cache the list of installed plugins."""
        if self._plugins is None:
            self._plugins = []
            if not os.environ.get('OCT_DISABLE_PLUGINS', False) and  self.plugin_list_file.exists():
                with open(self.plugin_list_file) as f:
                    self._plugins = json.load(f)
        return self._plugins

    @property
    def installed_pkgs(self) -> dict:
        """Get/cache the installed packages."""
        if self._installed is None:
            self._installed = {}
            if self.installed_file.exists():
                with open(self.installed_file) as f:
                    self._installed = json.load(f)

        return self._installed

    def save_plugin_list(self):
        """Save the list of installed plugins."""
        with open(self.plugin_list_file, 'w') as f:
            json.dump(self.plugins, f, indent=2)

    def save_installed(self):
        """Save the installed packages."""
        with open(self.installed_file, 'w') as f:
            json.dump(self.installed_pkgs, f, indent=2)

    def pip_install(self, name, version, extras: list| str = None, scope=GENERIC_SCOPE, force=False):
        """Use pip to install a package."""
        if scope not in self.scopes:
            logger.debug(f'Skipping {name}=={version} for scope {scope}')
            return
        if extras is None:
            extras = []
        elif isinstance(extras, str):
            extras = list(filter(None, extras.split(' ')))
        scoped_name = f'{scope}::{name}'
        # if name in DONE:
        #     if DONE[name] == vstring:
        #         return
        #     raise ValueError(f'Coneflict: {name}=={version} already installed as {DONE[name]}')
        # DONE[name] = vstring

        if not force and scoped_name in self.installed_pkgs:
            if self.installed_pkgs[scoped_name]['version'] == version:
                return

        ptr = {}
        self.installed_pkgs[scoped_name] = ptr
        ptr['version'] = version
        ptr['files'] = []
        ptr['dirs'] = []

        _pip_install(f'{name}=={version}', self.plugin_dir, extras)

        # print(f'  Installing {name}=={version}')

        tmp_dir = find_site_packages(self.plugin_dir)
        logger.debug(f'Package installed by pip in {tmp_dir}')
        for src in tmp_dir.iterdir():
            if src.name.endswith('__pycache__'):
                continue
            # shutil.move(d, PLUGIN_SP[scope])
            dst = self.PLUGIN_SP[scope] / src.name
            if src.is_file():
                ptr['files'].append(src.name)
                if dst.exists():
                    dst.unlink()
                shutil.move(src, dst)
            elif src.is_dir():
                ptr['dirs'].append(src.name)
                if dst.exists():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    shutil.rmtree(src)
                else:
                    shutil.move(src, dst)
            else:
                raise NotImplementedError(f'Unknown type: {src}')

        self.save_installed()

    def _install_plugin(self, name: str):
        """Run the `install` part of the plugin."""
        if not (data := self.get_plugin_data(name)):
            raise ValueError(f'Plugin {name} not found')
        pkg = data['package']
        version = data['version']
        deps = data.get('dependencies', [])

        logger.info(f'Installing plugin {pkg}=={version} with dependencies')
        for dep in deps[::-1]:
            self.pip_install(**dep)

        self.pip_install(pkg, version)

    def install_plugin(self, name: str):
        """Ensure the plugin is installed."""
        self._install_plugin(name)
        if name not in self.plugins:
            self.plugins.append(name)
            self.save_plugin_list()
        if name not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS.append(name)
        reload_django_apps()

    def uninstall_package(self, name: str):
        """Uninstall a package."""
        if name not in self.installed_pkgs:
            return
        logger.info(f'Uninstalling package {name}')
        ptr = self.installed_pkgs.pop(name)
        scope, _ = name.split('::')
        scope_dir = self.PLUGIN_SP[scope]
        for pth in ptr['files']:
            (scope_dir / pth).unlink()
        for pth in ptr['dirs']:
            shutil.rmtree(scope_dir / pth)

        self.save_installed()

    def uninstall_plugin(self, name: str):
        """Uninstall the plugin."""
        if name not in self.plugins:
            return
        data = self.get_plugin_data(name)
        pkg = data['package']
        scope = data.get('scope', GENERIC_SCOPE)
        scoped_name = f'{scope}::{pkg}'
        logger.info(f'Uninstalling plugin {scoped_name} and non-shared dependencies')
        # logger.debug(f'INSTALLED: {INSTALLED}')
        if scoped_name not in self.installed_pkgs:
            raise ValueError(f'Plugin {name} not installed')

        other_deps = set()
        plugin_deps = set()
        torm_deps = set()
        for plugin in self.plugins_data:
            deps = set(f"{_['scope']}::{_['name']}" for _ in plugin.get('dependencies', []))
            if plugin['name'] == name:
                plugin_deps |= deps
            else:
                other_deps |= deps
        torm_deps = plugin_deps - other_deps

        for dep in torm_deps:
            self.uninstall_package(dep)
        self.uninstall_package(scoped_name)

        self.plugins.remove(name)
        self.save_plugin_list()

        settings.INSTALLED_APPS.remove(name)
        reload_django_apps()
