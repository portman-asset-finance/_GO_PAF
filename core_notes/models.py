
import os
import re

from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    """
    Notes model.
    """

    _fields = (
        'type',
        'customer_id',
        'agreement_id',
        'entry',
        'user',
        'created',
        'updated'
    )

    # type of note entry
    type = models.CharField(max_length=50, null=True, blank=True)

    # customer id
    customer_id = models.CharField(max_length=10, null=True, blank=True)

    # agreement id
    agreement_id = models.CharField(max_length=10, null=True, blank=True)

    # actual note text
    entry = models.TextField()

    # param info
    params = models.TextField(max_length=50, null=True, blank=True)

    # django user
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    # follow up date
    follow_up = models.DateTimeField(null=True, blank=True)

    # archived
    archived = models.NullBooleanField(default=False)

    # created date
    created = models.DateTimeField(auto_now_add=True)

    # updated timestamp
    updated = models.DateTimeField(auto_now=True)

    def as_dict(self, **kwargs):
        row = {
            "id": self.id,
            "type": self.type,
            "customer_id": self.customer_id,
            "agreement_id": self.agreement_id,
            "entry": self.entry,
            "user": self.user,
            "created": self.created,
            "updated": self.updated,
            "follow_up": self.follow_up,
            "follow_up_date": '',
            'follow_up_time': ''
        }
        if kwargs.get("for_json"):
            row["created"] = row["created"].strftime("%d/%m/%Y %H:%M")
            row["updated"] = row["updated"].strftime("%d/%m/%Y %H:%M")
            if self.follow_up:
                split_follow_up = str(row['follow_up']).split(' ')
                row['follow_up_date'] = split_follow_up[0]
                row['follow_up_time'] = split_follow_up[1]
                row["follow_up"] = row["follow_up"].strftime("%d/%m/%Y at %H:%M")
            new_row = {}
            for f in row.keys():
                if row[f]:
                    new_row[f] = str(row[f])
                else:
                    new_row[f] = ''
            return new_row
        return row

    def get_fields(self):
        return self._fields

    class Meta:
        get_latest_by = "-created"


class Type(models.Model):
    """
    Note entry types.

    """

    # Textual representation of entry type.
    description = models.CharField(max_length=250)

    # Created timestamp
    created = models.DateTimeField(auto_now_add=True)

    # Updated timestamp
    updated = models.DateTimeField(auto_now=True)

    # Selectable
    selectable = models.NullBooleanField(default=True)

    # Level
    LEVEL_CHOICES = (
        ('Normal', 'Normal'),
        ('Customer', 'Customer'),
        ('Agreement', 'Agreement')
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True)

    def __str__(self):
        return self.description


class Asset(models.Model):
    """
    Assets model.

    """

    _fields = (
        'notes_id',
        'dir_name',
        'file_name',
        'original_file_name',
        'file_type',
        'created',
        'updated'
    )

    # customer id
    customer_id = models.CharField(max_length=10, null=True, blank=True)

    # agreement id
    agreement_id = models.CharField(max_length=10, null=True, blank=True)

    # notes foreign key
    note_id = models.ForeignKey(Note, on_delete=models.CASCADE, null=True)

    # file location
    dir_name = models.CharField(max_length=250)

    # file name
    file_name = models.CharField(max_length=250)

    # original file name
    original_file_name = models.CharField(max_length=250)

    # agreement doc
    agreement_doc = models.NullBooleanField(default=False)

    # file type
    file_type = models.CharField(max_length=250)

    # archived
    archived = models.NullBooleanField(default=False)

    # created date
    created = models.DateTimeField(auto_now_add=True)

    # updated timestamp
    updated = models.DateTimeField(auto_now=True)

    # user
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)

    def as_dict(self, **kwargs):
        row = {
            "id": self.id,
            "notes_id": self.note_id,
            "dir_name": self.dir_name,
            "file_name": self.file_name,
            "original_file_name": self.original_file_name,
            "file_type": self.file_type,
            "created": self.created,
            "updated": self.updated,
            "on_disk": 0,
            "is_pdf": 0,
            "user": self.user,
            "archived": self.archived
        }
        if os.path.isfile("{}\\{}".format(self.dir_name, self.file_name)):
            row["on_disk"] = 1
        if re.search(r'pdf$', self.file_name):
            row["is_pdf"] = 1
        if kwargs.get("for_json"):
            row["created"] = row["created"].strftime("%d/%m/%Y at %H:%M")
            row["updated"] = row["updated"].strftime("%d/%m/%Y at %H:%M")
            new_row = {}
            for f in row.keys():
                if not type(new_row) is int:
                    new_row[f] = str(row[f])
            return new_row
        return row


class Contacts(models.Model):

    contact_id = models.CharField(max_length=50, null=True, blank=True)
    contact_type = models.ForeignKey('ContactType', on_delete=models.DO_NOTHING, null=True, blank=True)
    contact_description = models.TextField(max_length=150, null=True, blank=True)
    contact_priority = models.CharField(max_length=50, null=True, blank=True)
    contact_customer_id = models.CharField(max_length=10, null=True, blank=True)
    contact_agreement_id = models.CharField(max_length=10, null=True, blank=True)
    contact_first_name = models.CharField(max_length=50, null=True, blank=True)
    contact_surname = models.CharField(max_length=50, null=True, blank=True)
    contact_address_line1 = models.CharField(max_length=50, null=True, blank=True)
    contact_address_line2 = models.CharField(max_length=50, null=True, blank=True)
    contact_address_line3 = models.CharField(max_length=50, null=True, blank=True)
    contact_address_line4 = models.CharField(max_length=50, null=True, blank=True)
    contact_address_line5 = models.CharField(max_length=50, null=True, blank=True)
    contact_postcode = models.CharField(max_length=10, null=True, blank=True)
    contact_mobile_number = models.CharField(max_length=200, null=True, blank=True)
    contact_phone_number = models.CharField(max_length=200, null=True, blank=True)
    contact_email = models.CharField(max_length=200, null=True, blank=True)

    guarantor_info = models.CharField(max_length=150, null=True, blank=True)

    contact_social_media1 = models.CharField(max_length=50, null=True, blank=True)
    contact_social_media2 = models.CharField(max_length=50, null=True, blank=True)
    contact_social_media3 = models.CharField(max_length=50, null=True, blank=True)

    params = models.TextField(max_length=50, null=True, blank=True)
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    archived = models.NullBooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.contact_id)


class ContactType(models.Model):

    contact_type_code = models.CharField(max_length=10 , null=True, blank=True)

    contact_type_description = models.CharField(max_length=250)

    selectable = models.NullBooleanField(default=True)

    def __str__(self):
        return '{} ({})'.format(self.contact_type_description, self.contact_type_code)