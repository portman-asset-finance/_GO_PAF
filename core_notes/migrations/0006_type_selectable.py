# Generated by Django 2.0.9 on 2019-05-30 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_notes', '0005_asset_agreement_doc'),
    ]

    operations = [
        migrations.AddField(
            model_name='type',
            name='selectable',
            field=models.NullBooleanField(default=True),
        ),
    ]
