
from .models import Contacts, ContactType

from .functions_notes_validatecontact import validate_mobile_number, validate_phone_number, validate_email_addr


def generate_contact_id():
    iterator = Contacts.objects.all().count()
    while True:
        iterator += 1
        ref = "CNF{}".format(iterator)
        if Contacts.objects.filter(contact_id=ref).count() == 0:
            return ref


def validate_contact(data, err_obj):
    """
    Validation for creating/updating a contact.

    :param data: POST data
    :param err_obj: response error object passed to the template
    :return: True if passed else None
    """

    error_count = 0

    if not data.get('contact_type').strip():
        error_count += 1
        err_obj['contact_type'] = 'Contact Type Required'
        return

    phone_or_email_only = False
    if data.get('contact_type') == 'Phone/Email Only':
        phone_or_email_only = True

    if not data.get('contact_priority').strip():
        error_count += 1
        err_obj['contact_priority'] = 'Priority Required'

    if phone_or_email_only:
        if not data.get('contact_description'):
            err_obj['contact_description'] = 'Contact Description Required.'
            error_count += 1

        # if not data.get('contact_mobile').strip() and not data.get('contact_phone').strip() and not data.get('contact_email').strip() and not data.get('contact_description'):
        #     error_count += 3
        #     err_obj['contact_phone'] = 'Mobile or Phone or Email Required'
        #     err_obj['contact_mobile'] = 'Mobile or Phone or Email Required'
        #     err_obj['contact_email'] = 'Mobile or Phone or Email Required'

    else:
        if not data.get('contact_first_name').strip():
            error_count += 1
            err_obj['contact_first_name'] = 'Please enter a first name'

        if not data.get('contact_last_name').strip():
            error_count += 1
            err_obj['contact_last_name'] = 'Please enter a last name'

        if not data.get('contact_postcode').strip():
            error_count += 1
            err_obj['contact_postcode'] = 'Please enter a postcode'

        if not data.get('contact_address_1').strip():
            error_count += 1
            err_obj['contact_address_1'] = 'Please enter an address line 1'

        if not data.get('contact_mobile').strip() and not data.get('contact_phone').strip():
            error_count += 1
            err_obj['contact_phone'] = 'Mobile or Phone Required'
            err_obj['contact_mobile'] = 'Mobile or Phone Required'

        if data.get('contact_mobile').strip():
            if not validate_mobile_number(data['contact_mobile'], err_obj, 'contact_mobile'):
                error_count += 1

        if data.get('contact_phone').strip():
            if not validate_phone_number(data['contact_phone'], err_obj, 'contact_phone'):
                error_count += 1

        if data.get('contact_email').strip():
            if not validate_email_addr(data['contact_email'], err_obj, 'contact_email'):
                error_count += 1

    if error_count:
        return

    return True


def build_contact_object_from_template(request):

    contact = {
        'contact_id': request.POST.get('contact_id') or generate_contact_id(),
        'last_updated_by': request.user,
        'contact_type': ContactType.objects.get(contact_type_description=request.POST.get('contact_type')),
        'contact_priority': request.POST.get('contact_priority'),
        'contact_customer_id': request.POST.get('customer_id'),
        'contact_agreement_id': request.POST.get('agreement_id'),
        'contact_first_name': request.POST.get('contact_first_name'),
        'contact_surname': request.POST.get('contact_last_name'),
        'contact_address_line1': request.POST.get('contact_address_1'),
        'contact_address_line2': request.POST.get('contact_address_2'),
        'contact_address_line3': request.POST.get('contact_address_3'),
        'contact_address_line4': request.POST.get('contact_address_4'),
        'contact_address_line5': request.POST.get('contact_address_5'),
        'contact_postcode': request.POST.get('contact_postcode'),
        'contact_mobile_number': request.POST.get('contact_mobile'),
        'contact_phone_number': request.POST.get('contact_phone'),
        'contact_email': request.POST.get('contact_email'),
        'contact_social_media1': request.POST.get('social_media1'),
        'contact_social_media2': request.POST.get('social_media2'),
        'contact_social_media3': request.POST.get('social_media3'),
        'guarantor_info': request.POST.get('contact_guarantor_info'),
        'contact_description': request.POST.get('contact_description')
    }

    return contact
