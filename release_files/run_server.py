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
import importlib
import os
import subprocess

req_version = os.environ.get('OCT_VERSION', '0.7.3').lower()

def install_upgrade(upgrade=False):
    """Install or upgrade the ocr_translate package."""
    cmd = ['pip', 'install']
    if upgrade:
        print(f'Upgrading ocr_translate to {req_version}...')
        cmd.append('--upgrade')
    else:
        print(f'Installing ocr_translate {req_version}...')
    if req_version in ['latest', 'last']:
        cmd.append('django-ocr_translate')
    else:
        cmd.append(f'django-ocr_translate=={req_version}')
    subprocess.run(cmd, check=True)
    print('...done')

if os.environ.get('OCT_AUTOUPDATE', 'false').lower() in ['true', 't', '1']:
    install_upgrade(upgrade=True)

try:
    run = importlib.import_module('ocr_translate.scripts.run')
except ImportError:
    print('`ocr_translate` not found: installing django-ocr_translate...')
    install_upgrade()
    importlib.invalidate_caches()
    run = importlib.import_module('ocr_translate.scripts.run')

if __name__ == '__main__':
    run.main()
