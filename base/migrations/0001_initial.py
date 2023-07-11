# Generated by Django 4.2.2 on 2023-07-11 09:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BBox',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('l', models.IntegerField()),
                ('b', models.IntegerField()),
                ('r', models.IntegerField()),
                ('t', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('md5', models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('iso1', models.CharField(max_length=2, unique=True)),
                ('iso2b', models.CharField(max_length=3, unique=True)),
                ('iso2t', models.CharField(max_length=3, unique=True)),
                ('iso3', models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='OCRBoxModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='OCRModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('languages', models.ManyToManyField(related_name='ocr_models', to='base.language')),
            ],
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TSLModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('dst_languages', models.ManyToManyField(related_name='tsl_models_dst', to='base.language')),
                ('src_languages', models.ManyToManyField(related_name='tsl_models_src', to='base.language')),
            ],
        ),
        migrations.CreateModel(
            name='TranslationRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('options', models.JSONField()),
                ('lang_dst', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_trans', to='base.language')),
                ('lang_src', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_trans', to='base.language')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runs', to='base.tslmodel')),
                ('result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_trans', to='base.text')),
                ('text', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_trans', to='base.text')),
            ],
        ),
        migrations.CreateModel(
            name='OCRRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('options', models.JSONField()),
                ('bbox', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_ocr', to='base.bbox')),
                ('lang_src', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_ocr', to='base.language')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runs', to='base.ocrmodel')),
                ('result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_ocr', to='base.text')),
            ],
        ),
        migrations.CreateModel(
            name='OCRBoxRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('options', models.JSONField()),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_ocr', to='base.image')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runs', to='base.ocrboxmodel')),
            ],
        ),
        migrations.AddField(
            model_name='bbox',
            name='from_ocr',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='base.ocrboxrun'),
        ),
        migrations.AddField(
            model_name='bbox',
            name='image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bboxes', to='base.image'),
        ),
    ]
