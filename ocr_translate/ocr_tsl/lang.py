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
"""Manages the globaly selected source and destination language."""
from .. import models as m

LANG_SRC = None
LANG_DST = None

def get_lang_src():
    """Return the source language."""
    return LANG_SRC

def get_lang_dst():
    """Return the destination language."""
    return LANG_DST

def load_lang_src(iso1):
    """Load the source language."""
    global LANG_SRC
    LANG_SRC = m.Language.objects.get(iso1=iso1)

def load_lang_dst(iso1):
    """Load the destination language."""
    global LANG_DST
    LANG_DST = m.Language.objects.get(iso1=iso1)
