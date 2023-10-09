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
"""Manages the globaly selected source and destination language tries."""
import json
import logging
from importlib import resources

from .trie import Trie

TRIE_SRC = None
# TRIE_DST = None

logger = logging.getLogger('ocr.general')

def get_trie_src():
    """Return the source language trie."""
    return TRIE_SRC

# def get_trie_dst():
#     """Return the destination language trie."""
#     return TRIE_DST

def load_trie(iso1: str) -> Trie | None:
    """Load a trie."""
    trie_file = resources.files('ocr_translate.dictionaries').joinpath(f'{iso1}.txt')
    freq_file = resources.files('ocr_translate.dictionaries').joinpath(f'{iso1}_freq.json')

    if not trie_file.exists():
        logger.debug(f'No source language trie found: {iso1}')
        return None

    with freq_file.open(encoding='utf-8') as f:
        freq = json.load(f)

    logger.info(f'Loading source language trie: {iso1}')
    res = Trie()
    with trie_file.open(encoding='utf-8') as f:
        for word in f.read().splitlines():
            res.insert(word, freq.get(word, -1e-4))

    return res

def load_trie_src(iso1: str) -> None:
    """Load the source language trie."""
    global TRIE_SRC

    TRIE_SRC = load_trie(iso1)

# def load_trie_dst(iso1: str) -> None:
#     """Load the destination language trie."""
#     global TRIE_DST

#     TRIE_DST = load_trie(iso1)
