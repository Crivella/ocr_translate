# Generated by Django 4.2.2 on 2023-07-08 17:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_remove_text_lang_translationrun_lang_dst_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ocrrun',
            name='lang_src',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='from_ocr', to='base.language'),
            preserve_default=False,
        ),
    ]