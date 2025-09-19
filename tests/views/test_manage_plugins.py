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

import pytest
from django.urls import reverse

from ocr_translate import entrypoint_manager as epm
from ocr_translate import views
from ocr_translate.plugin_manager import PluginManager

pytestmark = pytest.mark.django_db


@pytest.fixture()
def post_kwargs():
    """Data for POST request."""
    return {
        'data': {
            'plugins': {},
        },
        'content_type': 'application/json',
    }

def test_manage_plugins_nonpost(client):
    """Test manage_plugins with non POST request."""
    url = reverse('ocr_translate:manage_plugins')
    response = client.get(url)
    assert response.status_code == 405

def test_manage_plugins_missing_required(client):
    """Test manage_plugins with POST request missing required attribute."""
    url = reverse('ocr_translate:manage_plugins')
    response = client.post(url)
    assert response.status_code == 400

@pytest.mark.parametrize('mock_called', [set()], indirect=True)
def test_manage_plugins_noaction(monkeypatch, mock_called, client, post_kwargs):
    """Test manage_plugins with POST request: no action taken."""
    monkeypatch.setattr(epm, 'get_group_entrypoints', mock_called)
    url = reverse('ocr_translate:manage_plugins')

    assert not hasattr(mock_called, 'called')
    response = client.post(url, **post_kwargs)
    assert response.status_code == 200
    assert mock_called.called

def test_manage_plugins_install(monkeypatch, epm_no_ept, mock_called, client, post_kwargs):
    """Test manage_plugins with POST request: install a plugin."""
    pmng = PluginManager()
    monkeypatch.setattr(pmng, 'install_plugin', mock_called)

    plugin_name = 'present'
    post_kwargs['data']['plugins'] = {plugin_name: True}
    url = reverse('ocr_translate:manage_plugins')
    assert not hasattr(mock_called, 'called')
    response = client.post(url, **post_kwargs)
    assert response.status_code == 200
    assert mock_called.called
    assert mock_called.args[0] == plugin_name

def test_manage_plugins_uninstall(monkeypatch, epm_no_ept, mock_called, client, post_kwargs):
    """Test manage_plugins with POST request: uninstall a plugin."""
    pmng = PluginManager()
    monkeypatch.setattr(pmng, 'uninstall_plugin', mock_called)

    plugin_name = 'absent'
    post_kwargs['data']['plugins'] = {plugin_name: False}
    url = reverse('ocr_translate:manage_plugins')
    assert not hasattr(mock_called, 'called')
    response = client.post(url, **post_kwargs)
    assert response.status_code == 200
    assert mock_called.called
    assert mock_called.args[0] == plugin_name

def test_manage_plugins_raises(monkeypatch, client, post_kwargs):
    """Test manage_plugins with POST request: uninstall a plugin."""
    msg = 'Test exception'
    def mock_raises():
        raise ValueError(msg)
    monkeypatch.setattr(views, 'ep_manager', mock_raises)

    url = reverse('ocr_translate:manage_plugins')
    response = client.post(url, **post_kwargs)
    assert response.status_code == 502
    assert msg in response.json().get('error', '')
