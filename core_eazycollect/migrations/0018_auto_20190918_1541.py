# Generated by Django 2.1.12 on 2019-09-18 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_eazycollect', '0017_auto_20190918_1514'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestlog',
            name='status_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='requestlog',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
