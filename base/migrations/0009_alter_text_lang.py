# Generated by Django 4.2.2 on 2023-07-07 14:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_alter_ocrrun_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='text',
            name='lang',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='texts', to='base.language'),
        ),
    ]
