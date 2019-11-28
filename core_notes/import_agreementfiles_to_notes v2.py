import os, shutil, mimetypes

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apellio_nwcf.settings")

application = get_wsgi_application()

import re
import string
import random

from django.contrib.auth.models import User

from core_notes.models import Asset as AssetMdl

from anchorimport.models import AnchorimportAgreement_QueryDetail

def list_files(startpath):
    wip_count = 0
    wip_target = 1
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        if level == 1:

            for filename in files:
                if '.pdf' in filename:

                    mylist = os.path.basename(root).split(" -")
                    wip_agreement = mylist[0]

                    if wip_agreement in filename:

                        try:
                            agreement_object = AnchorimportAgreement_QueryDetail.objects.get(agreementnumber=wip_agreement)

                            filename_and_path = str(startpath) + '/' + str(os.path.basename(root)) + '/' + str(filename)

                            new_file_name = "".join(
                                random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
                            new_file_name = "{}{}".format(new_file_name, re.search("\..+$", filename).group(0))

                            filename_and_path_archive = str(
                                'C:/apellio-apps/apellio_nwcf/core_notes/_assets/') \
                                                        + str(new_file_name)

                            assets_obj = {

                                'customer_id': agreement_object.agreementcustomernumber,
                                'agreement_id': wip_agreement.strip(),
                                'dir_name': 'C:/apellio-apps/apellio_nwcf/core_notes/_assets/',
                                'file_name': new_file_name,
                                'original_file_name': filename,
                                'file_type': mimetypes.MimeTypes().guess_type(filename_and_path_archive)[0],
                                'user': User.objects.get(username='steve.ismay')
                            }
                            AssetMdl.objects.create(**assets_obj)

                            shutil.copy(filename_and_path, filename_and_path_archive)
                            print(filename_and_path)
                            # wip_count = wip_count + 1
                            # if wip_count > wip_target:
                            #     break

                        except:

                            pass

            # if wip_count > wip_target:
            #     break


def restore_files(startpath):
    wip_count = 0
    wip_target = 100
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        if level == 1:

            mylist = os.path.basename(root).split(" -")
            wip_agreement = mylist[0]

            file_objects = AssetMdl.objects.filter(agreement_id=wip_agreement)

            for file_object in file_objects:
                filename = file_object.original_file_name
                target_filename_and_path = str(startpath) + '/' + str(os.path.basename(root)) + '/' + str(filename)
                # target_filename_and_path = str(
                # 'C:/_CDRIVE_APELLIO/_SERVER_UAT_GO_NWCF/UAT_STAGING_GO_NWCF/core_notes/test_restore/') \
                #                         + str(filename)
                filename_and_path_archive = str(
                'C:/_CDRIVE_APELLIO/apellio_nwcf/core_notes/_assets/') \
                                        + str(file_object.file_name)

                print(target_filename_and_path)
                print(filename_and_path_archive)
                shutil.copy(filename_and_path_archive, target_filename_and_path)
                wip_count = wip_count + 1
                if wip_count > wip_target:
                    break

            if wip_count > wip_target:
                break



list_files('//ncfsrv01-mk/Company/Alfandari Private Equities/_APEL Agreements')
