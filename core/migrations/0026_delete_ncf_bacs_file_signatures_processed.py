# Generated by Django 2.1.12 on 2019-10-25 11:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20191025_1130'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ncf_bacs_file_signatures_processed',
        ),
    ]
