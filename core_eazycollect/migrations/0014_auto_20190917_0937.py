# Generated by Django 2.1.12 on 2019-09-17 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_eazycollect', '0013_auto_20190916_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requesttemp',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
