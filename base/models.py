from django.db import models

# Create your models here.

lang_length = 16

class OCRModel(models.Model):
    """OCR model using hugging space naming convention"""
    name = models.CharField(max_length=128)

class OCRBoxModel(models.Model):
    """OCR model for bounding boxes"""
    name = models.CharField(max_length=128)

class TSLModel(models.Model):
    """Translation models using hugging space naming convention"""
    name = models.CharField(max_length=128)
    src_language = models.CharField(max_length=lang_length)
    dst_language = models.CharField(max_length=lang_length)

class Image(models.Model):
    """Image registered as the md5 of the uploaded file"""
    md5 = models.CharField(max_length=32, unique=True)

class BBox(models.Model):
    """Bounding box of a text in an image"""
    l = models.IntegerField()
    b = models.IntegerField()
    r = models.IntegerField()
    t = models.IntegerField()

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='bboxes')
    from_ocr = models.ForeignKey('OCRBoxRun', on_delete=models.CASCADE, related_name='result')

    @property
    def lbrt(self):
        return self.l, self.b, self.r, self.t
    
    def __str__(self):
        return f'{self.lbrt}'
    
class Text(models.Model):
    """Text extracted from an image or translated from another text"""
    text = models.TextField(unique=True)
    lang = models.CharField(max_length=lang_length)

class OCRBoxRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.JSONField()

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_ocr')
    model = models.ForeignKey(OCRBoxModel, on_delete=models.CASCADE, related_name='runs')
    # result = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='from_ocr')

class OCRRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.JSONField()

    # image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_ocr')
    bbox = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='to_ocr')
    model = models.ForeignKey(OCRModel, on_delete=models.CASCADE, related_name='runs')
    result = models.ForeignKey(
        Text, on_delete=models.CASCADE, related_name='from_ocr',
        null=True, blank=True,
        )

class TranslationRun(models.Model):
    """Translation run on a text using a specific model"""
    options = models.JSONField()
    
    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='to_trans')
    model = models.ForeignKey(TSLModel, on_delete=models.CASCADE, related_name='runs')
    result = models.ForeignKey(
        Text, on_delete=models.CASCADE, related_name='from_trans',
        null=True, blank=True,
        )

