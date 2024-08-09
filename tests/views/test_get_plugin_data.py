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
"""Test get_plugin_data serverside views.handshake."""
# pylint: disable=redefined-outer-name

from django.urls import reverse


def test_get_plugin_data_nonget(client):
    """Test get_plugin_data with non GET request."""
    url = reverse('ocr_translate:get_plugin_data')
    response = client.post(url)
    assert response.status_code == 405

def test_get_plugin_data(client):
    """Test get_plugin_data."""
    url = reverse('ocr_translate:get_plugin_data')
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    key = list(data.keys())[0]
    ptr = data[key]
    assert 'name' not in ptr
    assert 'description' in ptr
    assert 'version' in ptr
    assert 'installed' in ptr
    assert 'homepage' in ptr
