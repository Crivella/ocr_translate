from django.db import models

# Create your models here.

lang_length = 16

class Language(models.Model):
    """Language used for translation"""
    name = models.CharField(max_length=lang_length, unique=True)

    def __str__(self):
        return str(self.name)

class OCRModel(models.Model):
    """OCR model using hugging space naming convention"""
    name = models.CharField(max_length=128)
    languages = models.ManyToManyField(Language, related_name='ocr_models')

    def __str__(self):
        return str(self.name)

class OCRBoxModel(models.Model):
    """OCR model for bounding boxes"""
    name = models.CharField(max_length=128)

    def __str__(self):
        return str(self.name)

class TSLModel(models.Model):
    """Translation models using hugging space naming convention"""
    name = models.CharField(max_length=128)
    src_languages = models.ManyToManyField(Language, related_name='tsl_models_src')
    dst_languages = models.ManyToManyField(Language, related_name='tsl_models_dst')
    
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
    options = models.JSONField()

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_ocr')
    model = models.ForeignKey(OCRBoxModel, on_delete=models.CASCADE, related_name='runs')
    # result = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='from_ocr')

class OCRRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.JSONField()

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='from_ocr')

    # image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_ocr')
    bbox = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='to_ocr')
    model = models.ForeignKey(OCRModel, on_delete=models.CASCADE, related_name='runs')
    result = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_ocr')

class TranslationRun(models.Model):
    """Translation run on a text using a specific model"""
    options = models.JSONField()

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='from_trans')
    lang_dst = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='to_trans')
    
    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='to_trans')
    model = models.ForeignKey(TSLModel, on_delete=models.CASCADE, related_name='runs')
    result = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_trans')

