# Generated by Django 4.2 on 2024-10-13 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0008_rename_source_wastealarm_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='plantinfo',
            name='domain',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]