
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse, Http404
from django.core import serializers
from django.contrib.auth.decorators import login_required

from .apps import NotesConfig
from .notes import Notes

from .models import Note as NoteMdl
from .models import Type as TypeMdl
from .models import Asset as AssetMdl
from .models import Contacts
from .models import ContactType

from .functions import validate_contact, build_contact_object_from_template

from .templatetags.notes_extras import get_icon_for_note_asset

import re
import requests, json


@login_required(login_url=NotesConfig.login_url)
def main(request, **kwargs):
    """
    Handles all the requests for notes, including getting and updating
    existing records, and creating new ones.
    :param request: Django request object.
    :return: JSON or rendered HTML.
    """

    # TODO: Class-based views
    # Initialise Notes class with Django request object.
    notes_obj = Notes(request)

    if request.method == 'GET':
        if not kwargs:
            kwargs = request.GET.copy()
        notes_obj.get_records(**kwargs)
        # web_hook_url = 'https://hooks.zapier.com/hooks/catch/5361003/oo1aseo/'
        # msg = {'text': 'Alert from python'}
        # requests.post(web_hook_url, data=json.dumps(msg))

    elif request.method == 'POST' and request.POST.get('id'):
        notes_obj.update_record()
        # web_hook_url = 'https://hooks.zapier.com/hooks/catch/5361003/oo09gh4/'
        # msg = {'follow_up_date': request.POST.get("follow_up_date"),
        #        'follow_up_time': request.POST.get("follow_up_time"),
        #        'follow_up': request.POST.get("follow_up"),
        #        'customer_id': request.POST.get("customer_id"),
        #        'agreement_id': request.POST.get("agreement_id"),
        #        'type': request.POST.get("type"),
        #        'entry': request.POST.get("entry"),
        #        'user': request.user.username,
        #        }
        # requests.post(web_hook_url, data=json.dumps(msg))

    elif request.method == 'POST':
        notes_obj.create_record(**kwargs)
        # web_hook_url = 'https://hooks.zapier.com/hooks/catch/5361003/oo09gh4/'
        # msg = {'follow_up_date': request.POST.get("follow_up_date"),
        #         'follow_up_time': request.POST.get("follow_up_time"),
        #        'follow_up': request.POST.get("follow_up"),
        #        'customer_id': request.POST.get("customer_id"),
        #        'agreement_id': request.POST.get("agreement_id"),
        #        'type': request.POST.get("type"),
        #        'entry': request.POST.get("entry"),
        #        'user': request.user.username,
        #        }
        # requests.post(web_hook_url, data=json.dumps(msg))

    else:
        raise Exception("Unacceptable request method {}".format(request.method))

    return notes_obj.response()


@login_required(login_url=NotesConfig.login_url)
def type(request):
    """

    Returns a list of entry types to populate on screen.

    :param request:
    :return:

    """

    if request.is_ajax():

        data = []

        for row in TypeMdl.objects.filter(selectable=True):
            data.append(row.description)

        return JsonResponse(data, safe=False)

    raise Http404()


@login_required(login_url=NotesConfig.login_url)
def asset(request, asset_id):
    """
    Deals with returning assets to the screen.
    :param request:
    :return:
    """

    assets_obj = AssetMdl.objects.get(id=asset_id)

    if assets_obj.archived:
        raise Http404()

    try:

        if request.method == 'GET':

            file = open("{}/{}".format(assets_obj.dir_name, assets_obj.file_name), "rb+").read()

            response = HttpResponse(file, content_type=assets_obj.file_type)
            if re.search(r'pdf$', assets_obj.original_file_name):
                response['Content-Disposition'] = 'filename="{}"'.format(assets_obj.original_file_name)
            else:
                response['Content-Disposition'] = 'attachment; filename="{}"'.format(assets_obj.original_file_name)

            return response

        elif request.method == 'DELETE':

            assets_obj.archived = True
            assets_obj.save()

            return JsonResponse({'success': True})

    except Exception as e:
        print(e)
        raise Http404()


@login_required(login_url=NotesConfig.login_url)
def note(request, note_id):
    """
    Returns a single note via Json
    """

    note_obj = NoteMdl.objects.get(id=note_id)

    data = note_obj.as_dict(for_json=True)

    data['files'] = []

    for file in AssetMdl.objects.filter(note_id=note_obj):
        file_obj = file.as_dict(for_json=True)
        file_obj['icon'] = get_icon_for_note_asset(file.original_file_name)
        data['files'].append(file_obj)

    return JsonResponse(data, safe=False)


@login_required(login_url=NotesConfig.login_url)
def upload_asset(request):

    kwargs = {
        'customer_id': request.POST.get('customer_id'),
        'agreement_id': request.POST.get('agreement_id')
    }
    Notes(request).process_file(request.FILES.get('file'), **kwargs)

    return JsonResponse({})


@login_required(login_url=NotesConfig.login_url)
def create_or_update_contact(request):

    context = {
        'error': '',  # Global error
        'errors': {},  # Errors related to individual input fields
        'values': request.POST.copy(),  # Values entered,
        'contact_id': '',
        'contact_types': ContactType.objects.filter(selectable=True)
    }

    customer_id = request.GET.get('customer_id')

    if request.method == 'GET':
        data = {
            'html': render_to_string('includes/input-contacts-modal.html', context=context)
        }
        return JsonResponse(data)

    if request.method == 'POST':

        # import pprint
        # pprint.pprint(request.POST)

        try:

            method = 'create'
            if request.POST.get('contact_id'):
                method = 'update'

            if validate_contact(context['values'], context['errors']):
                contact_obj = build_contact_object_from_template(request)
                if method == 'create':
                    contact_rec = Contacts(**contact_obj)
                    contact_rec.save()
                    context['contact_id'] = contact_rec.contact_customer_id
                elif method == 'update':
                    contact_rec = Contacts.objects.get(contact_id=request.POST['contact_id'])
                    contact_obj_keys = contact_obj.keys()
                    if request.POST.get('contact_type') == 'Phone/Email Only':
                        contact_obj_keys = ('contact_type', 'contact_priority', 'contact_email', 'contact_mobile_number', 'contact_phone_number', 'contact_description')
                    for key in contact_obj_keys:
                        setattr(contact_rec, key, contact_obj[key])
                    contact_rec.save()
                    context['contact_id'] = contact_rec.contact_customer_id

        except Exception as e:
            context['error'] = str(e)

        data = {}

        if context['error'] or context['errors']:
            contact_context = context.copy()
            context['contact'] = contact_context
            data['html'] = render_to_string('includes/input-contacts-modal.html', context=context)
            return JsonResponse(data)

        context['values'] = ''

        return JsonResponse({'success': True})

    notes_kwargs = {
        'customer_id': customer_id
    }
    if request.POST.get('agreement_id'):
        notes_kwargs['agreement_id'] = request.POST['agreement_id']

    return Notes(request).get_records(**notes_kwargs).response(contact_context=context)


@login_required(login_url=NotesConfig.login_url)
def manage_contact(request, contact_id):

    if request.is_ajax():

        if request.method == 'GET':

            contact = Contacts.objects.get(id=contact_id)

            data = serializers.serialize('json', [contact])

            data = data.strip("[]")

            return JsonResponse({'data': data, 'contact_type': contact.contact_type.contact_type_description})

        if request.method == 'DELETE':

            contact = Contacts.objects.get(id=contact_id)

            contact.archived = True

            contact.save()

            return JsonResponse({'success': True})

    raise Http404()
