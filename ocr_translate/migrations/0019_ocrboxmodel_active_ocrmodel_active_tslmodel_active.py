# Generated by Django 5.1 on 2024-08-09 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr_translate', '0018_ocrmodel_processor_name_ocrmodel_tokenizer_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='ocrboxmodel',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='ocrmodel',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='tslmodel',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
