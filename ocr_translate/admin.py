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
