# Generated by Django 4.2 on 2024-09-10 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0002_alter_wasteimpurity_event_uid_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wasteimpurity',
            name='img_id',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='wastematerial',
            name='img_id',
            field=models.CharField(max_length=255),
        ),
    ]
