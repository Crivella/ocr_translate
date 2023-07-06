from django.contrib import admin

from . import models as m

# Register your models here.

class OCRBoxModelAdmin(admin.ModelAdmin):
    list_display = ('name',)

class OCRModelAdmin(admin.ModelAdmin):
    list_display = ('name',)

class TSLModelAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(m.OCRBoxModel, OCRBoxModelAdmin)
admin.site.register(m.OCRModel, OCRModelAdmin)
admin.site.register(m.TSLModel, TSLModelAdmin)
