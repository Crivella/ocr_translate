# Generated by Django 4.2.2 on 2023-07-10 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0015_alter_language_iso1_alter_language_iso2b_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='language',
            name='iso3',
            field=models.CharField(max_length=32, unique=True),
        ),
    ]
