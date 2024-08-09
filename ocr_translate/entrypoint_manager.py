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
from .ocr_tsl.signals import refresh_model_cache_signal

logger = logging.getLogger('ocr.general')

def get_ep_groups() -> list[str]:
    """Get groups of entrypoint related to app"""
    return [_ for _ in entry_points().keys() if _.startswith('ocr_translate.')]

def get_all_entrypoints() -> set[tuple[str, str]]:
    """Get all entrypoints for the app"""
    return set((group, ep.name) for group in get_ep_groups() for ep in entry_points(group=group))

def get_group_entrypoints(group: str) -> set[EntryPoint]:
    """Get all entrypoints for a group"""
    return set(ep for ep in entry_points(group=group))

GROUPS = {
    'ocr_translate.box_data': (m.OCRBoxModel, ini.add_box_model),
    'ocr_translate.ocr_data': (m.OCRModel, ini.add_ocr_model),
    'ocr_translate.tsl_data': (m.TSLModel, ini.add_tsl_model),
}

@contextlib.contextmanager
def ep_manager():
    """Context manager for entrypoint management"""
    before: dict[str, set] = {}
    for grp in GROUPS:
        before[grp] = get_group_entrypoints(grp)

    yield

    after: dict[str, set] = {}
    for grp in GROUPS:
        after[grp] = get_group_entrypoints(grp)

    flag = False
    for grp, data in GROUPS.items():
        cls, create_func = data
        added = after[grp] - before[grp]
        for ept in added:
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
            logger.info(f'Entrypoint {ept.name} removed')
            data = ept.load()
            model_id = data['name']
            try:
                model = cls.objects.get(name=model_id)
                model.active = False
                model.save()
            except cls.DoesNotExist:
                logger.warning(f'Could not find model {model_id} to deactivate')
                continue

        flag = flag or bool(added or removed)

    if flag:
        refresh_model_cache_signal.send(sender=None)
