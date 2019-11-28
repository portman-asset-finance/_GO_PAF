
from .apps import CoreBounceConfig


def upload_bacs_file(django_request_file_object):

    file = django_request_file_object

    if file:
        with open("{}/{}".format(CoreBounceConfig.bacs_assets_directory, file.name), "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    return True

def upload_datacash_file(django_request_file_object):

    file = django_request_file_object

    if file:
        with open("{}/{}".format(CoreBounceConfig.datacash_assets_directory, file.name), "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    return True
