# Generated by Django 2.0.9 on 2019-06-26 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_dd_drawdowns', '0007_batchlock_session_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='batchheaders',
            name='sagewisdom_processed',
            field=models.NullBooleanField(default=False),
        ),
    ]
