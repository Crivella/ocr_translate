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
from django.db import models

lang_length = 32

class OptionDict(models.Model):
    """Dictionary of options for OCR and translation"""
    options = models.JSONField(unique=True)

    def __str__(self):
        return str(self.options)

class Language(models.Model):
    """Language used for translation"""
    name = models.CharField(max_length=64, unique=True)
    iso1 = models.CharField(max_length=8, unique=True)
    iso2b = models.CharField(max_length=8, unique=True)
    iso2t = models.CharField(max_length=8, unique=True)
    iso3 = models.CharField(max_length=32, unique=True)

    easyocr = models.CharField(max_length=32, null=True)
    tesseract = models.CharField(max_length=32, null=True)
    facebookM2M = models.CharField(max_length=32, null=True)

    break_chars = models.CharField(max_length=512, null=True)
    ignore_chars = models.CharField(max_length=512, null=True) 

    def __str__(self):
        return str(self.iso1)

class OCRModel(models.Model):
    """OCR model using hugging space naming convention"""
    name = models.CharField(max_length=128)
    languages = models.ManyToManyField(Language, related_name='ocr_models')

    language_format = models.CharField(max_length=32, null=True)

    def __str__(self):
        return str(self.name)

class OCRBoxModel(models.Model):
    """OCR model for bounding boxes"""
    name = models.CharField(max_length=128)
    languages = models.ManyToManyField(Language, related_name='box_models')

    language_format = models.CharField(max_length=32, null=True)

    def __str__(self):
        return str(self.name)

class TSLModel(models.Model):
    """Translation models using hugging space naming convention"""
    name = models.CharField(max_length=128)
    src_languages = models.ManyToManyField(Language, related_name='tsl_models_src')
    dst_languages = models.ManyToManyField(Language, related_name='tsl_models_dst')

    language_format = models.CharField(max_length=32, null=True)
    
    def __str__(self):
        return str(self.name)

class Image(models.Model):
    """Image registered as the md5 of the uploaded file"""
    md5 = models.CharField(max_length=32, unique=True)

class BBox(models.Model):
    """Bounding box of a text in an image"""
    l = models.IntegerField(null=False)
    b = models.IntegerField(null=False)
    r = models.IntegerField(null=False)
    t = models.IntegerField(null=False)

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='bboxes')
    from_ocr = models.ForeignKey('OCRBoxRun', on_delete=models.CASCADE, related_name='result')

    @property
    def lbrt(self):
        return self.l, self.b, self.r, self.t
    
    def __str__(self):
        return f'{self.lbrt}'
    
class Text(models.Model):
    """Text extracted from an image or translated from another text"""
    text = models.TextField()
    # lang = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='texts')

class OCRBoxRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='ocr_box_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='box_src')

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_box')
    model = models.ForeignKey(OCRBoxModel, on_delete=models.CASCADE, related_name='box_runs')
    # result = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='from_ocr')

class OCRRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='ocr_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='ocr_src')

    # image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_ocr')
    bbox = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='to_ocr')
    model = models.ForeignKey(OCRModel, on_delete=models.CASCADE, related_name='ocr_runs')
    result = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_ocr')
    
class TranslationRun(models.Model):
    """Translation run on a text using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='trans_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='trans_src')
    lang_dst = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='trans_dst')
    
    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='to_trans')
    model = models.ForeignKey(TSLModel, on_delete=models.CASCADE, related_name='tsl_runs')
    result = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_trans')
    

