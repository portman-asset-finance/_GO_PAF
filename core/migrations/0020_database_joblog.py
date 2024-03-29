# Generated by Django 2.1.12 on 2019-10-11 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20191011_1059'),
    ]

    operations = [
        migrations.CreateModel(
            name='database_joblog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_name', models.CharField(blank=True, max_length=250, null=True)),
                ('job_start_datetime', models.DateTimeField(blank=True, null=True)),
                ('job_end_datetime', models.DateTimeField(blank=True, null=True)),
                ('job_ended', models.CharField(blank=True, max_length=1, null=True)),
            ],
            options={
                'verbose_name': 'Database Joblog',
                'verbose_name_plural': 'Database Joblogs',
                'ordering': ('job_name',),
            },
        ),
    ]
