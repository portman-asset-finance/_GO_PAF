# Generated by Django 2.0.9 on 2019-06-26 10:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core_sage_export', '0014_auto_20190626_1134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sagebatchtransactions',
            name='include',
        ),
    ]
