# Generated by Django 4.2 on 2024-09-10 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wasteimpurity',
            name='event_uid',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='wastematerial',
            name='event_uid',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='wastesegments',
            name='event_uid',
            field=models.CharField(max_length=255),
        ),
    ]
