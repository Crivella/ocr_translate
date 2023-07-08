# Generated by Django 4.2.2 on 2023-07-08 17:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0010_alter_text_text'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text',
            name='lang',
        ),
        migrations.AddField(
            model_name='translationrun',
            name='lang_dst',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='to_trans', to='base.language'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='translationrun',
            name='lang_src',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='from_trans', to='base.language'),
            preserve_default=False,
        ),
    ]
