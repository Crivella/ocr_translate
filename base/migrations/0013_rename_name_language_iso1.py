# Generated by Django 4.2.2 on 2023-07-09 13:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0012_ocrrun_lang_src'),
    ]

    operations = [
        migrations.RenameField(
            model_name='language',
            old_name='name',
            new_name='iso1',
        ),
    ]
