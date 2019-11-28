
import re


def validate_mobile_number(mobile, err_obj, err_key):
    """
    Validates a given mobile number

    """

    mobile = re.sub(re.compile('\s+'), '', mobile)

    if not mobile:
        err_obj[err_key] = 'Mobile Number Required'
        return

    if len(mobile) > 11:
        err_obj[err_key] = 'Max 11 digits long.'
        return

    if len(mobile) < 10:
        err_obj[err_key] = 'Min 10 digits long.'
        return

    # if mobile[:2] != '07':
    #     err_obj[err_key] = 'Mobile Number must start with a 07'
    #     return

    # if not re.search(r'^\\d+$', mobile):
    #     err_obj[err_key] = 'Mobile Number must contain digits only'
    #     return

    return True


def validate_phone_number(phone, err_obj, err_key):
    """
    Validates a given mobile number

    """

    phone = re.sub(re.compile('\s+'), '', phone)

    if not phone:
        err_obj[err_key] = 'Phone Number Required'
        return

    if len(phone) > 11:
        err_obj[err_key] = 'Max 11 digits long.'
        return

    if len(phone) < 10:
        err_obj[err_key] = 'Min 10 digits long.'
        return

    # if not re.search(r'^\\d+$', phone):
    #     err_obj[err_key] = 'Phone Number must contain digits only'
    #     return

    return True


def validate_email_addr(email, err_obj, err_key):
    """
    Validate a given email address

    """

    if not email:
        err_obj[err_key] = 'Email Address Required'
        return

    if not re.match('[^@]+@[^@]+\.[^@]+', email):
        err_obj[err_key] = 'Invalid Email Address'
        return

    return True











