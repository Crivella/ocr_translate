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
"""Manages changes in entrypoints after installation/removal of plugins."""

import contextlib
import logging
from importlib.metadata import EntryPoint, entry_points

from . import models as m
from .ocr_tsl import initializers as ini
from .ocr_tsl.box import get_box_model, unload_box_model
from .ocr_tsl.ocr import get_ocr_model, unload_ocr_model
from .ocr_tsl.signals import refresh_model_cache_signal
from .ocr_tsl.tsl import get_tsl_model, unload_tsl_model

logger = logging.getLogger('ocr.general')

def get_group_entrypoints(group: str) -> set[EntryPoint]:
    """Get all entrypoints for a group"""
    return set(ep for ep in entry_points(group=group))

GROUPS = {
    'ocr_translate.box_data': (m.OCRBoxModel, ini.add_box_model, get_box_model, unload_box_model),
    'ocr_translate.ocr_data': (m.OCRModel, ini.add_ocr_model, get_ocr_model, unload_ocr_model),
    'ocr_translate.tsl_data': (m.TSLModel, ini.add_tsl_model, get_tsl_model, unload_tsl_model),
}

@contextlib.contextmanager
def ep_manager():
    """Context manager for entrypoint management.
    Provides a context that monitors changes to server server specific entrypoints.
    Make sures models from added entrypoints are created/activated and models from removed
    entrypoints are deactivated.
    """
    before: dict[str, set] = {}
    for grp in GROUPS:
        before[grp] = get_group_entrypoints(grp)

    yield

    after: dict[str, set] = {}
    for grp in GROUPS:
        after[grp] = get_group_entrypoints(grp)

    flag = False
    for grp, data in GROUPS.items():
        cls, create_func, get_func, unload_func = data
        loaded_model = get_func()
        added = after[grp] - before[grp]
        # Using after to ensure that when using same plugin folder with new db, the models are created
        for ept in after[grp]:
            if ept in added:
                logger.info(f'New entrypoint {ept.name} found')
            data = ept.load()
            model_id = data['name']
            try:
                model = cls.objects.get(name=model_id)
            except cls.DoesNotExist:
                model = create_func(data.copy())
            model.active = True
            model.save()

        removed = before[grp] - after[grp]
        for ept in removed:
            data = ept.load()
            model_id = data['name']
            try:
                model = cls.objects.get(name=model_id)
                if loaded_model is not None:
                    if loaded_model.name == model.name:
                        unload_func()
                model.active = False
                model.save()
                logger.info(f'Entrypoint {ept.name} removed')
            except cls.DoesNotExist:
                logger.warning(f'Could not find model {model_id} to deactivate')
                continue

        flag = flag or bool(added or removed)

    if flag:
        refresh_model_cache_signal.send(sender=None)
