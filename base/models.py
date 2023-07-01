from django.db import models

# Create your models here.

lang_length = 16

class OCRmodel(models.Model):
    """OCR model using hugging space naming convention"""
    name = models.CharField(max_length=128)

class Image(models.Model):
    """Image registered as the md5 of the uploaded file"""
    md5 = models.CharField(max_length=32, unique=True)

class Text(models.Model):
    """Text extracted from an image or translated from another text"""
    text = models.TextField(unique=True)
    lang = models.CharField(max_length=lang_length)

class Translators(models.Model):
    """Translation models using hugging space naming convention"""
    name = models.CharField(max_length=128)
    src_language = models.CharField(max_length=lang_length)
    dst_language = models.CharField(max_length=lang_length)

class OCRRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.JSONField()

    source = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_ocr')
    medium = models.ForeignKey(OCRmodel, on_delete=models.CASCADE, related_name='runs')
    dest   = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_ocr')

class TranslationRun(models.Model):
    """Translation run on a text using a specific model"""
    text = models.TextField()

    options = models.JSONField()
    
    source = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='to_trans')
    medium = models.ForeignKey(Translators, on_delete=models.CASCADE, related_name='runs')
    dest   = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_trans')

    def __str__(self):
        return self.text
    
