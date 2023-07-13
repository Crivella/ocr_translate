# Generated by Django 4.2.2 on 2023-07-13 19:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_remove_ocrboxrun_options_remove_ocrrun_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ocrboxrun',
            name='options',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ocr_box_options', to='base.optiondict'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ocrrun',
            name='options',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ocr_options', to='base.optiondict'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='translationrun',
            name='options',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='trans_options', to='base.optiondict'),
            preserve_default=False,
        ),
    ]
