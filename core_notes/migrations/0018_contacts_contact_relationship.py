# Generated by Django 2.0.9 on 2019-06-18 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_notes', '0017_auto_20190613_1427'),
    ]

    operations = [
        migrations.AddField(
            model_name='contacts',
            name='contact_relationship',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
