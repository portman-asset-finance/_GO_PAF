# Generated by Django 2.0.9 on 2019-06-20 09:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core_notes', '0018_contacts_contact_relationship'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contacts',
            old_name='contact_relationship',
            new_name='guarantor_info',
        ),
    ]
