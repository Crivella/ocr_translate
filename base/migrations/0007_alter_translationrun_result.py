# Generated by Django 4.2.2 on 2023-07-07 14:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_remove_translationrun_dst_lang_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='translationrun',
            name='result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_trans', to='base.text'),
        ),
    ]
