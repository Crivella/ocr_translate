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
"""Admin interface for ocr_translate app."""
from importlib.metadata import entry_points

from django import forms
from django.contrib import admin

from . import models as m


class LanguageAdmin(admin.ModelAdmin):
    """Admin interface for Language model"""
    list_display = ('name', 'iso1', 'iso2b', 'iso2t', 'iso3')

class OCRBoxModelForm(forms.ModelForm):
    """Form for OCRBoxModel model"""
    entrypoint = forms.ChoiceField(
        choices=[(ep.name, ep.name) for ep in entry_points(group=m.OCRBoxModel.entrypoint_namespace)]
        )

class OCRModelForm(forms.ModelForm):
    """Form for OCRModel model"""
    entrypoint = forms.ChoiceField(
        choices=[(ep.name, ep.name) for ep in entry_points(group=m.OCRModel.entrypoint_namespace)]
        )

class TSLModelForm(forms.ModelForm):
    """Form for TSLModel model"""
    entrypoint = forms.ChoiceField(
        choices=[(ep.name, ep.name) for ep in entry_points(group=m.TSLModel.entrypoint_namespace)]
        )
class OCRBoxModelAdmin(admin.ModelAdmin):
    """Admin interface for OCRBoxModel model"""
    list_display = ('name',)
    filter_horizontal = ('languages',)
    form = OCRBoxModelForm

class OCRModelAdmin(admin.ModelAdmin):
    """Admin interface for OCRModel model"""
    list_display = ('name',)
    filter_horizontal = ('languages',)
    form = OCRModelForm

class TSLModelAdmin(admin.ModelAdmin):
    """Admin interface for TSLModel model"""
    list_display = ('name',)
    filter_horizontal = ('src_languages', 'dst_languages')
    form = TSLModelForm


admin.site.register(m.Language, LanguageAdmin)
admin.site.register(m.OCRBoxModel, OCRBoxModelAdmin)
admin.site.register(m.OCRModel, OCRModelAdmin)
admin.site.register(m.TSLModel, TSLModelAdmin)
