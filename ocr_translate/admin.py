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
from django.contrib import admin

from . import models as m

# Register your models here.

class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso1', 'iso2b', 'iso2t', 'iso3')

class OCRBoxModelAdmin(admin.ModelAdmin):
    list_display = ('name',)

class OCRModelAdmin(admin.ModelAdmin):
    list_display = ('name',)

class TSLModelAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(m.Language, LanguageAdmin)
admin.site.register(m.OCRBoxModel, OCRBoxModelAdmin)
admin.site.register(m.OCRModel, OCRModelAdmin)
admin.site.register(m.TSLModel, TSLModelAdmin)
