# Generated by Django 4.2 on 2024-09-23 13:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0005_remove_filter_title_remove_filteritem_item_value'),
    ]

    operations = [
        migrations.CreateModel(
            name='WasteAlarm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=100)),
                ('timestamp', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event_uid', models.CharField(max_length=255)),
                ('delivery_id', models.CharField(blank=True, max_length=255, null=True)),
                ('confidence_score', models.FloatField()),
                ('severity_level', models.IntegerField()),
                ('img_id', models.CharField(max_length=255)),
                ('img_file', models.CharField(max_length=255)),
                ('model_name', models.CharField(max_length=255)),
                ('model_tag', models.CharField(max_length=255)),
                ('meta_info', models.JSONField(blank=True, null=True)),
                ('edge_box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.edgeboxinfo')),
            ],
            options={
                'verbose_name_plural': 'Waste Alarm',
                'db_table': 'waste_alar,',
            },
        ),
    ]
