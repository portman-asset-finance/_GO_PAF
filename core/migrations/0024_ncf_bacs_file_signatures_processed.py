# Generated by Django 2.1.12 on 2019-10-25 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20191015_1715'),
    ]

    operations = [
        migrations.CreateModel(
            name='ncf_bacs_file_signatures_processed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_signature', models.CharField(max_length=10000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'BACS File Signatures Processed',
                'verbose_name_plural': '< 1.03.1 BACS File Signatures Processed',
                'ordering': ('created_at',),
            },
        ),
    ]