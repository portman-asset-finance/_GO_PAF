# Generated by Django 2.0.9 on 2019-07-11 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_notes', '0020_auto_20190710_1540'),
    ]

    operations = [
        migrations.AddField(
            model_name='contacts',
            name='contact_description',
            field=models.TextField(blank=True, max_length=150, null=True),
        ),
    ]
