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
"""Fixtures for ocr_tsl tests"""

import pytest


@pytest.fixture()
def mock_base_model():
    """Mock BaseModel class."""
    class MockModel(): # pylint: disable=invalid-name
        """Mocked BaseModel class."""
        def __init__(self):
            self.load_called = False
            self.unload_called = False
        def load(self): # pylint: disable=missing-function-docstring
            self.load_called = True
        def unload(self): # pylint: disable=missing-function-docstring
            self.unload_called = True

    return MockModel
