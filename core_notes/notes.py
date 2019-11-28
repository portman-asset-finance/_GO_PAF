import re
import string
import random
import datetime

from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, reverse

from django.db.models import Q
from django.utils.html import strip_tags
from django.contrib.auth.models import User

from .apps import NotesConfig

from .models import Note as NoteMdl
from .models import Type as TypeMdl
from .models import Asset as AssetMdl

from .models import Contacts
from .models import ContactType

# SWI 2019-06-26 - Target Apellio Data Schema rather than GO Native.
from core_agreement_crud.models import go_agreement_querydetail, go_customers
# from anchorimport.models import AnchorimportAgreement_QueryDetail, AnchorimportCustomers


class Notes(object):
    """
    Notes class.

    """

    _request = None
    _notes_fields = NoteMdl().get_fields()

    data = []
    files = {}
    contacts = []

    context = {}
    display_message = False
    customer_id = None
    agreement_id = None

    def __init__(self, request=None):
        """
        Initialize the Notes object with the Django request object.

        :param request: Django request object.
        """
        self._request = request
        if request.POST.get('customer_id'):
            self.customer_id = request.POST['customer_id']
        if request.GET.get('customer_id'):
            self.customer_id = request.GET['customer_id']
        if request.POST.get('agreement_id'):
            self.agreement_id = request.POST['agreement_id']
        if request.GET.get('agreement_id'):
            self.agreement_id = request.GET['agreement_id']

        if request.session.get('customer_id'):
            if request.session['customer_id'] == self.customer_id:
                self.display_message = False
            else:
                self.display_message = True
                request.session['customer_id'] = self.customer_id
        else:
            request.session['customer_id'] = self.customer_id
            self.display_message = True

    def get_records(self, **kwargs):
        """
        Get's notes via the notes model.
        :param kwargs:
        :return:
        """

        self.data = []
        self.contacts = []

        # Build search object.
        search_obj = {}
        for f in self._notes_fields:
            if f in kwargs and kwargs.get(f):
                if type(kwargs[f]) is list:
                    if kwargs[f][0]:
                        search_obj[f] = kwargs[f][0]
                else:
                    search_obj[f] = kwargs[f]

        self.customer_id = search_obj['customer_id']
        self.context = search_obj.copy()
        self.context['has_pinned'] = False

        # Execute search
        # =============================
        if search_obj:

            if search_obj.get('agreement_id'):
                agreement_id = search_obj['agreement_id']
                del(search_obj['agreement_id'])
                notes_queryset = NoteMdl.objects.filter(Q(agreement_id=agreement_id) |
                                                        Q(agreement_id__isnull=True), **search_obj).exclude()
                search_obj['agreement_id'] = agreement_id
            else:
                notes_queryset = NoteMdl.objects.filter(agreement_id__isnull=True, **search_obj)

            for row in notes_queryset.order_by("-created"):
                data = row.as_dict(for_json=True)
                data['files'] = []
                if data['type'] == 'Pinned Note':
                    self.context['has_pinned'] = data['id']
                self.data.append(data)
        else:
            for row in NoteMdl.objects.all().order_by("-created"):
                data = row.as_dict(for_json=True)
                data['files'] = []
                self.data.append(data)

        # Files
        # =============================

        self.files['customer'] = []
        self.files['agreement'] = []

        # 1) Get Customer Files
        for file in AssetMdl.objects.filter(customer_id=search_obj['customer_id'], note_id__isnull=True,
                                            agreement_id__isnull=True).exclude(archived=True).order_by('-id'):
            self.files['customer'].append(file.as_dict(for_json=True))

        # 2) Get Agreement Files
        if search_obj.get('agreement_id'):
            for file in AssetMdl.objects.filter(customer_id=search_obj['customer_id'],
                                                agreement_id=search_obj.get('agreement_id'),
                                                note_id__isnull=True).exclude(archived=True).order_by('-id'):
                self.files['agreement'].append(file.as_dict(for_json=True))
        else:
            for file in AssetMdl.objects.filter(customer_id=search_obj['customer_id'],
                                                agreement_id__isnull=False,
                                                note_id__isnull=True).exclude(archived=True).order_by('-id'):
                self.files['agreement'].append(file.as_dict(for_json=True))

        # 3) Get Note files
        for note in self.data:
            note['text_entry'] = strip_tags(note['entry'])
            for file in AssetMdl.objects.filter(note_id=note['id']).exclude(archived=True):
                file_row = file.as_dict(for_json=True)
                if note['agreement_id']:
                    self.files['agreement'].append(file_row)
                else:
                    self.files['customer'].append(file_row)
                # note['files'].append(file.as_dict(for_json=True))

        # 4) Get Contacts
        self.contacts = []
        for contact in Contacts.objects.filter(contact_customer_id=search_obj['customer_id'], archived=False).order_by('contact_priority', '-updated'):
            self.contacts.append(contact)

        return self

    def create_record(self, **kwargs):
        """
        Create's a new note entry via the Notes model and processes any files uploaded.
        :param kwargs:
        :return:
        """

        # TODO: Django Forms.

        # Build entry object.
        entry_obj = {}
        for f in ('customer_id', 'entry', 'type', 'agreement_id', 'params', 'follow_up'):
            entry_obj[f] = self._request.POST.get(f, None)
            if not entry_obj[f] and f != 'entry':
                del entry_obj[f]

        if entry_obj['type'] == 'Customer Note':
            if entry_obj.get('agreement_id'):
                del(entry_obj['agreement_id'])

        if entry_obj['type'] == 'Pinned Note':
            if 'agreement_id' in entry_obj:
                del(entry_obj['agreement_id'])

        # User model.
        entry_obj['user'] = User.objects.get(username=self._request.user.username)

        # Create notes record.
        note_obj = NoteMdl.objects.create(**entry_obj)

        # Process assets.
        if self._request.FILES:
            i = 1
            while True:
                file_param = "file{}".format(i)
                if self._request.FILES.get(file_param):
                    file = self._request.FILES[file_param]
                    self.process_file(file, note_obj=note_obj)
                    i = i + 1
                else:
                    break
            for file in self._request.FILES.getlist('files'):
                self.process_file(file, note_obj=note_obj)

        return self

    def process_file(self, file, **kwargs):
        """
        File Upload processing.

        """
        new_file_name = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        new_file_name = "{}{}".format(new_file_name, re.search("\..+$", file.name).group(0))
        with open("{}\{}".format(NotesConfig.assets_directory, new_file_name), "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        assets_obj = {
            'note_id': kwargs.get('note_obj'),
            'customer_id': kwargs.get('customer_id'),
            'agreement_id': kwargs.get('agreement_id'),
            'dir_name': NotesConfig.assets_directory,
            'file_name': new_file_name,
            'original_file_name': file.name,
            'file_type': file.content_type,
            'user': User.objects.get(username=self._request.user.username)
        }
        AssetMdl.objects.create(**assets_obj)
        return assets_obj

    def update_record(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        _id = self._request.POST['id']

        # Build Entry Object
        entry_obj = {}
        for f in ('entry', 'agreement_id', 'type', 'params', 'follow_up'):
            entry_obj[f] = self._request.POST.get(f, None)

        if entry_obj['type'] == 'Customer Note':
            entry_obj['agreement_id'] = None

        if entry_obj['type'] == 'Pinned Note':
            entry_obj['agreement_id'] = None

        entry_obj['created'] = datetime.datetime.now()

        if not entry_obj['follow_up']:
            entry_obj['follow_up'] = None

        # Get User
        entry_obj['user'] = self._request.user

        # Update
        notes_obj = NoteMdl.objects.get(id=_id)
        for f in entry_obj.keys():
            setattr(notes_obj, f, entry_obj[f])
        notes_obj.save()

        return self

    def response(self, contact_context=None):
        """
        Handles the response, depending on the request type.
        :return:
        """

        if self._request.is_ajax():
            return JsonResponse(self.data, safe=False)

        if self._request.method == 'POST' and not contact_context:
            url = reverse('notes:main') + '?customer_id={}'.format(self.customer_id)
            if self.agreement_id:
                url += '&agreement_id={}'.format(self.agreement_id)
            return redirect(url)

        context = self.context

        # Get all agreements for this customer

        customer_agreements = []

        recs = go_agreement_querydetail.objects.filter(agreementcustomernumber=self.customer_id)
        for rec in recs:
            if context.get('agreement_id'):
                if rec.agreementnumber == context['agreement_id']:
                    context['agreement_detail'] = rec
            customer_agreements.append(rec.agreementnumber)

        context.update({
            'data': self.data,
            'files': self.files,
            'contacts': self.contacts,
            'note_types': [],
            'contact_types': [],
            'display_message': self.display_message,
            'agreements': customer_agreements,
            'customer_detail': go_customers.objects.get(customernumber=self.customer_id)
        })

        for row in TypeMdl.objects.filter(selectable=True).order_by('description'):
            # if context.get('has_pinned'):
            #     if row.description == 'Pinned Note':
            #         continue
            if (self.agreement_id) \
                    or (not self.agreement_id and row.level != 'Agreement') \
                        or row.level == 'Normal':
                context['note_types'].append(row.description.strip())

        for row in ContactType.objects.all():
            context['contact_types'].append(row.contact_type_description)

        if contact_context and type(contact_context) is dict:
            context.update({'contact': contact_context})

        return render(self._request, 'v2/view_notes.html', context)

        # raise Http404()
