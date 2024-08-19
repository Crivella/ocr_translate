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
"""Django routing for the ocr_translate app."""
from django.urls import path

from ocr_translate import views

app_name = 'ocr_translate'
urlpatterns = [
    path('', views.handshake, name='handshake'),
    path('set_models/', views.set_models, name='set_models'),
    path('set_lang/', views.set_lang, name='set_lang'),
    path('get_trans/', views.get_translations, name='get_trans'),
    path('run_tsl/', views.run_tsl, name='run_tsl'),
    path('run_tsl_xua', views.run_tsl_get_xunityautotrans, name='run_tsl_get_xunityautotrans'),
    path('run_ocrtsl/', views.run_ocrtsl, name='run_ocrtsl'),
    path('set_manual_translation/', views.set_manual_translation, name='set_manual_translation'),
    path('get_active_options/', views.get_active_options, name='get_active_options'),
    path('get_plugin_data/', views.get_plugin_data, name='get_plugin_data'),
    path('manage_plugins/', views.manage_plugins, name='manage_plugins'),
]
