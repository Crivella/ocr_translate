# Generated by Django 4.2.2 on 2023-07-10 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0016_alter_language_iso3'),
    ]

    operations = [
        migrations.AlterField(
            model_name='language',
            name='name',
            field=models.CharField(max_length=64, unique=True),
        ),
    ]
