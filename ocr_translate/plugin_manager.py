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

import functools
import json
import logging
import os
import platform
import shutil
import site
import subprocess
import sys
import time
from importlib import resources
from pathlib import Path
from threading import Lock

from django.apps import apps
from django.conf import settings

GENERIC_SCOPE = 'generic'
DEFAULT_OCT_BASE_DIR: Path = Path.home() / '.ocr_translate'

logger = logging.getLogger('ocr.general')

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

def get_safe_name(name: str) -> str:
    """Get a safe name for the plugin."""
    return name.replace('-', '_min_')

def install_overrides_decorator(func):
    """Decorator to install a package."""
    arg_names = ['version', 'extras', 'scope', 'system']

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        args = list(args)
        cls = args.pop(0)
        if args:
            if 'name' in kwargs:
                raise TypeError('Got multiple values for argument name')
            name = args.pop(0)
        elif 'name' in kwargs:
            name = kwargs.pop('name')
        else:
            raise ValueError('Name required')

        new_args = {'name': name}
        for val,key in zip(args, arg_names):
            new_args[key] = val
        for key, val in kwargs.items():
            if key in new_args:
                raise  TypeError(f'Got multiple values for argument {key}')
            new_args[key] = val

        safe_name = get_safe_name(name).upper()
        for key in arg_names:
            over_name = f'OCT_PKG_{safe_name}_{key.upper()}'
            if over_name in os.environ:
                logger.debug(f'Overriding {key} for {name} with {os.environ[over_name]}')
                new_args[key] = os.environ[over_name]

        return func(cls, **new_args)

    return wrapped

def _pip_install(package: str, prefix: str, extras: list[str] = None, retries: int = 3):
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
    attempts = 0
    while True:
        attempts += 1
        try:
            res = subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            if attempts <= retries:
                logger.error(
                    f'Error installing {package}, retrying {attempts}/{retries}. '
                    'Waiting 5s before retrying...'
                    )
                time.sleep(5)
                continue
            logger.error(f'Error installing {package}')
            logger.error(exc.stdout.decode())
            logger.error(exc.stderr.decode())
            raise exc
        break
    logger.debug(res.stdout.decode())

class PluginManager:  # pylint: disable=too-many-instance-attributes
    """Manage the plugins."""
    _SINGLETON = None

    device: str = None
    scopes: list[str] = None

    base_dir: Path = None
    plugin_dir: Path = None
    PLUGIN_SP: dict[str, Path] = {}

    plugin_list_file: Path = None
    installed_file: Path = None

    def __new__(cls, *args, **kwargs):
        if not cls._SINGLETON:
            cls._SINGLETON = super().__new__(cls, *args, **kwargs)
        return cls._SINGLETON

    def __init__(self):
        """Initialize the plugin manager."""
        self.device = os.environ.get('DEVICE', 'cpu')
        self.scopes = [GENERIC_SCOPE, self.device]
        self.base_dir = Path(os.environ.get('OCT_BASE_DIR', DEFAULT_OCT_BASE_DIR))
        self.plugin_dir = self.base_dir / 'plugins'

        self.plugin_list_file = self.base_dir / 'plugins.json'
        self.installed_file = self.plugin_dir / 'installed.json'

        self.disabled = os.environ.get('OCT_DISABLE_PLUGINS', False)

        self.lock_plugin = Lock()
        self.lock_pkg = Lock()

        self._plugins = None
        self._plugin_data = None
        self._installed = None
        self.system = platform.system().lower()

        self.ensure_pip()
        self.initialize_scopes()

        # Ensure no previous empty or wrong site-packages dirs are present
        while (tmp_dir := find_site_packages(self.plugin_dir)) is not None:
            shutil.rmtree(tmp_dir)

    def ensure_pip(self):
        """Ensure pip is installed."""
        if self.disabled:
            return
        try:
            subprocess.run(['pip', '-V'], capture_output=True, check=True)
        except FileNotFoundError as exc:
            msg = ' ---- '.join([
                '!!!!!'
                'pip not found, please install a version of python https://www.python.org/downloads/'
                'Make sure to check the `Add python.exe to PATH` checkbox during installation.'
            ])
            logger.error(msg)
            raise FileNotFoundError(msg) from exc

    @property
    def plugins_data(self) -> list[dict]:
        """Get/cache the plugin data."""
        if self.disabled:
            return []
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
        if self.disabled:
            return
        for scope in self.scopes:
            pth = self.plugin_dir / scope
            pth.mkdir(exist_ok=True, parents=True)
            self.PLUGIN_SP[scope] = pth
            sys.path.insert(0, pth.as_posix())
            logger.debug(f'Added {pth} to sys.path')
        sys.path_importer_cache.clear()

        site.USER_BASE = self.plugin_dir.as_posix()
        site.USER_SITE = self.PLUGIN_SP[GENERIC_SCOPE].as_posix()

    @property
    def plugins(self) -> list[str]:
        """Get/cache the list of installed plugins."""
        if self.disabled:
            return []
        if self._plugins is None:
            self._plugins = []
            if self.plugin_list_file.exists():
                with open(self.plugin_list_file) as f:
                    self._plugins = json.load(f)
        return self._plugins

    @property
    def installed_pkgs(self) -> dict:
        """Get/cache the installed packages."""
        if self.disabled:
            return {}
        if self._installed is None:
            self._installed = {}
            if self.installed_file.exists():
                with open(self.installed_file) as f:
                    self._installed = json.load(f)

        return self._installed

    def save_plugin_list(self):
        """Save the list of installed plugins."""
        if self.disabled:
            return
        with open(self.plugin_list_file, 'w') as f:
            json.dump(self.plugins, f, indent=2)

    def save_installed(self):
        """Save the installed packages."""
        if self.disabled:
            return
        with open(self.installed_file, 'w') as f:
            json.dump(self.installed_pkgs, f, indent=2)

    @install_overrides_decorator
    def install_package(
            self,
            name: str,
            version: str,
            extras: list| str = None,
            scope: str = GENERIC_SCOPE,
            system: str = '',
            ):
        """Install a package."""
        with self.lock_pkg:
            if scope not in self.scopes:
                # logging.debug(f'Skipping {name}=={version} for scope {scope}')
                logger.debug(f'Skipping {name}=={version} for scope {scope}')
                return
            if system and system.lower() != self.system:
                logger.debug(f'Skipping {name}=={version} for system {system}')
                return

            if extras is None:
                extras = []
            elif isinstance(extras, str):
                extras = list(filter(None, extras.split(' ')))
            scoped_name = f'{scope}::{name}'

            if scoped_name in self.installed_pkgs:
                if self.installed_pkgs[scoped_name]['version'] == version:
                    logger.debug(f'{scoped_name}=={version} already installed')
                    return
                logger.debug(f'Uninstalling {scoped_name}=={self.installed_pkgs[scoped_name]["version"]}')
                self._uninstall_package(scoped_name)

            ptr = {}
            self.installed_pkgs[scoped_name] = ptr
            ptr['version'] = version
            ptr['files'] = []
            ptr['dirs'] = []

            _pip_install(f'{name}=={version}', self.plugin_dir, extras)

            tmp_dir = find_site_packages(self.plugin_dir)
            if tmp_dir is None:
                raise FileNotFoundError(f'Could not find site-packages in {self.plugin_dir}')
            logger.debug(f'Package installed in {tmp_dir}')
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

            # Make sure only one site-packages dir exists after installing a package
            shutil.rmtree(tmp_dir)

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
            self.install_package(**dep)

        self.install_package(pkg, version)

    def install_plugin(self, name: str):
        """Ensure the plugin is installed."""
        with self.lock_plugin:
            self._install_plugin(name)
            if name not in self.plugins:
                self.plugins.append(name)
                self.save_plugin_list()
            if name not in settings.INSTALLED_APPS:
                settings.INSTALLED_APPS.append(name)
            reload_django_apps()

    def _uninstall_package(self, name: str):
        """Uninstall a package."""
        if name not in self.installed_pkgs:
            return
        logger.info(f'Uninstalling package {name}')
        scope, _ = name.split('::')
        if scope not in self.scopes:
            logger.debug(f'Skipping {name} for scope {scope}')
            return
        ptr = self.installed_pkgs.pop(name)
        scope_dir = self.PLUGIN_SP[scope]
        for pth in ptr['files']:
            (scope_dir / pth).unlink()
        for pth in ptr['dirs']:
            shutil.rmtree(scope_dir / pth)

        self.save_installed()


    def uninstall_package(self, name: str):
        """Uninstall a package thread safe."""
        with self.lock_pkg:
            self._uninstall_package(name)

    def uninstall_plugin(self, name: str):
        """Uninstall the plugin."""
        with self.lock_plugin:
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
                if plugin['name'] not in self.plugins:
                    continue
                deps = set()
                for dep in plugin.get('dependencies', []):
                    deps.add(f"{dep.get('scope', GENERIC_SCOPE)}::{dep['name']}")
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
