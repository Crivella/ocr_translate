# Generated by Django 4.2.2 on 2023-07-07 14:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_alter_translationrun_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ocrrun',
            name='result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_ocr', to='base.text'),
        ),
    ]