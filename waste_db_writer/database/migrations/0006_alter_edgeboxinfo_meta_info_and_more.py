# Generated by Django 4.2 on 2024-05-16 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0005_alter_edgeboxinfo_meta_info_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='edgeboxinfo',
            name='meta_info',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='plantinfo',
            name='meta_info',
            field=models.JSONField(blank=True, null=True),
        ),
    ]