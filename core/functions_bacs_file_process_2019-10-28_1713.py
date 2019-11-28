from django.core.exceptions import ObjectDoesNotExist
from zipfile import ZipFile, is_zipfile
import xml.etree.ElementTree as ET
import pytz, os, shutil, datetime
from datetime import timedelta
from decimal import Decimal

from core_bounce.apps import CoreBounceConfig

from .functions_shared import app_get_agreement_id, write_account_history

from .models import ncf_bacs_files_to_process, \
                    ncf_bacs_files_processed, \
                    ncf_bacs_reasons, \
                    ncf_auddis_addacs_advices, \
                    ncf_udd_advices, \
                    ncf_ddic_advices, \
                    ncf_bacs_ddic_reasons, \
                    go_extensions

from core_agreement_crud.models import go_account_transaction_summary

def app_process_bacs_files():

    all_paths = ncf_bacs_files_to_process.objects.all()

    # Step 01 - Extract all zip archives
    for path in all_paths:

        if path.network_path_source:
            wip_network_path_source = CoreBounceConfig.bacs_assets_directory + path.network_path_source
        else:
            wip_network_path_source = CoreBounceConfig.bacs_assets_directory

        if path.network_path_archive:
            wip_network_path_archive = CoreBounceConfig.bacs_assets_directory + path.network_path_archive
        else:
            wip_network_path_archive = CoreBounceConfig.bacs_assets_directory

        if path.file_type == 'zip':
            # Process zip files first and extract to the same directory. Then move the file to the archive folder.
            for dirpath, directories, filenames in os.walk(wip_network_path_source):
                for filename in filenames:
                    filename_and_path = str(dirpath) + str(filename)
                    filename_and_path_archive = str(wip_network_path_archive) + str(filename)
                    if os.path.splitext(filename)[1] != ".xlsx" and is_zipfile(filename_and_path):
                        try:
                            ncf_bacs_files_processed.objects.get(file_name=filename)
                            shutil.move(filename_and_path, filename_and_path_archive)
                            pass
                        except ObjectDoesNotExist:
                            with ZipFile(filename_and_path, 'r') as zip:
                                zip.extractall(dirpath)
                            shutil.move(filename_and_path, filename_and_path_archive)
                            write_to_filesprocessed = ncf_bacs_files_processed.objects.create(file_name=filename)
                break

    # Step 02 - Process all xml files
    for path in all_paths:
        if path.network_path_source:
            wip_network_path_source = CoreBounceConfig.bacs_assets_directory + path.network_path_source
        else:
            wip_network_path_source = CoreBounceConfig.bacs_assets_directory

        if path.network_path_archive:
            wip_network_path_archive = CoreBounceConfig.bacs_assets_directory + path.network_path_archive
        else:
            wip_network_path_archive = CoreBounceConfig.bacs_assets_directory

        if path.file_type == 'xml':
            # Process all required xml files
            for dirpath, directories, filenames in os.walk(wip_network_path_source):
                for filename in filenames:
                    # if the filename in the folder contains the file identifier from OSFilesTOProcess
                    if path.file_identifier in filename:
                        # Get the full path and file for source and archive
                        filename_and_path = str(dirpath) + str(filename)
                        filename_and_path_archive = str(wip_network_path_archive) + str(filename)

                        try:

                            ncf_bacs_files_processed.objects.get(file_name=filename)
                            shutil.move(filename_and_path, filename_and_path_archive)

                            pass

                        except ObjectDoesNotExist:

                            # Get the xml tree for the retrieved file
                            dd_xml_tree = ET.parse(filename_and_path)
                            root = dd_xml_tree.getroot()

                            if path.target_data_format == 'xml-01':

                                for elem in root.iter('MessagingAdvice'):
                                    val_reference = elem.attrib.get('reference')
                                    val_payer_name = elem.attrib.get('payer-name')
                                    val_reason_code = elem.attrib.get('reason-code')
                                    val_payer_sort_code = elem.attrib.get('payer-sort-code')
                                    val_payer_account_number = elem.attrib.get('payer-account-number')
                                    val_payer_new_sort_code = elem.attrib.get('payer-new-sort-code')
                                    val_payer_new_account_number = elem.attrib.get('payer-new-account-number')
                                    val_effective_date = elem.attrib.get('effective-date')
                                    val_due_date = elem.attrib.get('due-date')

                                    # write new row
                                    new_addacs = ncf_auddis_addacs_advices.objects.create(dd_reference=val_reference,
                                                               dd_payer_name=val_payer_name,
                                                               dd_reason_code=val_reason_code,
                                                               dd_payer_sort_code=val_payer_sort_code,
                                                               dd_payer_account_number=val_payer_account_number,
                                                               dd_payer_new_sort_code=val_payer_new_sort_code,
                                                               dd_payer_new_account_number=val_payer_new_account_number,
                                                               dd_effective_date=val_effective_date,
                                                               dd_due_date=val_due_date,
                                                               file_name=filename)

                            if path.target_data_format == 'xml-02':

                                for elem in root.iter('ReturnedDebitItem'):
                                    val_reference = elem.attrib.get('ref')
                                    val_original_process_date = elem.attrib.get('originalProcessingDate')
                                    val_transcode = elem.attrib.get('transCode')
                                    val_currency = elem.attrib.get('currency')
                                    val_value = elem.attrib.get('valueOf')
                                    val_return_description = elem.attrib.get('returnDescription')

                                    for elem1 in elem.findall('PayerAccount'):

                                        val_payer_sort_code = elem1.attrib.get('sortCode')
                                        val_payer_account_number = elem1.attrib.get('number')

                                        # write new row
                                        new_udd = ncf_udd_advices.objects.create(dd_reference=val_reference,
                                                                    dd_original_process_date=val_original_process_date,
                                                                    dd_transcode=val_transcode,
                                                                    dd_currency=val_currency,
                                                                    dd_value=val_value,
                                                                    dd_return_description=val_return_description,
                                                                    dd_payer_sort_code = val_payer_sort_code,
                                                                    dd_payer_account_number = val_payer_account_number,
                                                                    file_name=filename)

                                        # Get associated agreement
                                        wip_agreement_id = app_get_agreement_id(val_reference)

                                        # Get the associated schedule date
                                        wip_transaction_summary_extract = go_account_transaction_summary.objects\
                                                            .filter(agreementnumber=wip_agreement_id,
                                                            transactionsourceid__in=['GO1','GO3', 'SP1', 'SP2', 'SP3'],
                                                            transactiondate__gte=val_original_process_date)\
                                                            .order_by('transactiondate').first()

                                        if not wip_transaction_summary_extract:
                                            wip_transaction_summary_extract = go_account_transaction_summary.objects \
                                                .filter(agreementnumber=wip_agreement_id,
                                                        transactionsourceid__in=['GO1', 'GO3', 'SP1', 'SP2', 'SP3']) \
                                                .order_by('transactiondate').last()


                                        # Call Function to write Account History
                                        write_account_history(wip_agreement_id,
                                                              wip_transaction_summary_extract.transactiondate,
                                                              'GO9',
                                                              '12',
                                                              'Col',
                                                              val_value,
                                                              'GROSS',
                                                              wip_transaction_summary_extract.transnetpaymentinterest,
                                                              wip_transaction_summary_extract.transnetpaymentcapital,
                                                              None,
                                                              'Returned DD (' + val_return_description + ')')

                            if path.target_data_format == 'xml-03':

                                for DDICAdvice in root.iter('NewAdvices'):

                                    for alltags in DDICAdvice.findall('DDICAdvice'):

                                        wip_decimal = DDICAdvice.find('TotalValueOfDebits').text
                                        val_TotalValueOfDebits = Decimal(wip_decimal.replace(",", ""))
                                        val_DateOfDebit = DDICAdvice.find('DateOfDebit').text

                                        val_seqno = alltags.find('SeqNo').text
                                        val_PayingBankReference = alltags.find('PayingBankReference').text
                                        val_SUReference = alltags.find('SUReference').text
                                        val_ReasonCode = alltags.find('ReasonCode').text
                                        val_PayerSortCode = alltags.find('PayerSortCode').text
                                        val_PayerName = alltags.find('PayerName').text
                                        val_PayerAccount = alltags.find('PayerAccount').text
                                        wip_decimal = alltags.find('TotalAmount').text
                                        val_TotalAmount = Decimal(wip_decimal.replace(",", ""))

                                        for alltags1 in alltags.find('DDCollections'):

                                            val_DDIC_Type = 'DDICAdvice'
                                            val_DateOfDirectDebit = alltags1.find('DateOfDirectDebit').text
                                            wip_decimal = alltags1.find('Amount').text
                                            val_Amount = Decimal(wip_decimal.replace(",", ""))

                                            new_ddic = ncf_ddic_advices.objects.create(
                                            ddic_DDIC_Type=val_DDIC_Type,
                                            ddic_seqno = val_seqno,
                                            ddic_TotalDocumentValue = val_TotalValueOfDebits,
                                            ddic_DateOfDocumentDebit = val_DateOfDebit,
                                            ddic_PayingBankReference=val_PayingBankReference,
                                            ddic_SUReference =val_SUReference,
                                                ddic_Reason=ncf_bacs_ddic_reasons.objects.
                                                    get(ddic_reason_code=val_ReasonCode),
                                            ddic_PayerSortCode =val_PayerSortCode,
                                            ddic_PayerName =val_PayerName,
                                            ddic_PayerAccount =val_PayerAccount,
                                            ddic_TotalAmount =val_TotalAmount,
                                            ddic_DateOfOriginalDD=val_DateOfDirectDebit,
                                            ddic_OriginalDDAmount=val_Amount
                                            )

                                for CancelAdvice in root.iter('Cancellations'):

                                    for alltags in CancelAdvice.findall('DDICCancellation'):

                                        wip_decimal = CancelAdvice.find('TotalValueOfCancellations').text
                                        TotalValueOfCancellations = Decimal(wip_decimal.replace(",", ""))

                                        val_seqno = alltags.find('SeqNo').text
                                        val_PayingBankReference = alltags.find('PayingBankReference').text
                                        val_SUReference = alltags.find('SUReference').text
                                        val_ReasonCode = alltags.find('ReasonCode').text
                                        val_PayerSortCode = alltags.find('PayerSortCode').text
                                        val_PayerName = alltags.find('PayerName').text
                                        val_PayerAccount = alltags.find('PayerAccount').text
                                        wip_decimal = alltags.find('TotalAmount').text
                                        val_TotalAmount = Decimal(wip_decimal.replace(",", ""))

                                        for alltags1 in alltags.find('DDCollections'):

                                            val_DDIC_Type = 'DDICCancellation'
                                            val_DateOfDirectDebit = alltags1.find('DateOfDirectDebit').text
                                            wip_decimal = alltags1.find('Amount').text
                                            val_Amount = Decimal(wip_decimal.replace(",", ""))

                                            new_ddic = ncf_ddic_advices.objects.create(
                                                ddic_DDIC_Type=val_DDIC_Type,
                                                ddic_seqno=val_seqno,
                                                ddic_TotalDocumentValue=TotalValueOfCancellations,
                                                # ddic_DateOfDocumentDebit=val_DateOfDebit,
                                                ddic_PayingBankReference=val_PayingBankReference,
                                                ddic_SUReference=val_SUReference,
                                                ddic_Reason=ncf_bacs_ddic_reasons.objects.
                                                            get(ddic_reason_code=val_ReasonCode),
                                                ddic_PayerSortCode=val_PayerSortCode,
                                                ddic_PayerName=val_PayerName,
                                                ddic_PayerAccount=val_PayerAccount,
                                                ddic_TotalAmount=val_TotalAmount,
                                                ddic_DateOfOriginalDD=val_DateOfDirectDebit,
                                                ddic_OriginalDDAmount=val_Amount
                                            )

                            shutil.move(filename_and_path, filename_and_path_archive)
                            write_to_filesprocessed = ncf_bacs_files_processed.objects.create(file_name=filename)
                break

    # Step 99 - Process all unrequired files
    for path in all_paths:
        if path.network_path_source:
            wip_network_path_source = CoreBounceConfig.bacs_assets_directory + path.network_path_source
        else:
            wip_network_path_source = CoreBounceConfig.bacs_assets_directory

        if path.network_path_archive:
            wip_network_path_archive = CoreBounceConfig.bacs_assets_directory + path.network_path_archive
        else:
            wip_network_path_archive = CoreBounceConfig.bacs_assets_directory

        if path.file_identifier == '*ignore':
            for dirpath, directories, filenames in os.walk(wip_network_path_source):
                for filename in filenames:
                    filename_and_path = str(dirpath) + str(filename)
                    filename_and_path_archive = str(wip_network_path_archive) + str(filename)
                    shutil.move(filename_and_path, filename_and_path_archive)
                break

    # Go through and add agreement id to Auddis File
    go_extension = go_extensions.objects.get(ap_extension_code='auddis')
    empty_auddis_agreements = ncf_auddis_addacs_advices.objects.filter(agreement_id__isnull=True)
    for empty_auddis_agreement in empty_auddis_agreements:
        search_reference = empty_auddis_agreement.dd_reference
        wip_agreement_id = app_get_agreement_id(search_reference)

        empty_auddis_agreement.agreement_id = wip_agreement_id
        empty_auddis_agreement.save()

        d = empty_auddis_agreement.dd_effective_date
        if go_extension.ap_extension_last_interface_run < d:
            go_extension.ap_extension_last_interface_run = d
            go_extension.ap_extension_next_interface_run = \
                go_extension.ap_extension_last_interface_run + \
                timedelta(days=go_extension.ap_extension_required_interface_frequency_days)
            go_extension.save()

    # Go through and add agreement id to UDD File
    empty_udd_agreements = ncf_udd_advices.objects.filter(agreement_id__isnull=True)
    for empty_udd_agreement in empty_udd_agreements:
        search_reference = empty_udd_agreement.dd_reference
        wip_agreement_id = app_get_agreement_id(search_reference)

        empty_udd_agreement.agreement_id = wip_agreement_id
        empty_udd_agreement.save()

    # Go through and add agreement id to DDIC File
    empty_ddic_agreements = ncf_ddic_advices.objects.filter(agreement_id__isnull=True)
    for empty_ddic_agreement in empty_ddic_agreements:
        search_reference_01 = empty_ddic_agreement.ddic_SUReference.strip()
        search_reference = search_reference_01.replace(' ', '-')
        wip_agreement_id = app_get_agreement_id(search_reference)

        empty_ddic_agreement.agreement_id = wip_agreement_id
        empty_ddic_agreement.save()

    # Go through and add reason to Auddis File
    empty_reasons = ncf_auddis_addacs_advices.objects.filter(dd_reason__isnull=True)
    for empty_reason in empty_reasons:
        try:
            wip_reason = ncf_bacs_reasons.objects.get(reason_code=empty_reason.dd_reason_code).reason_description
        except ObjectDoesNotExist:
            wip_reason = "reason code undefined"

        empty_reason.dd_reason = wip_reason
        empty_reason.save()
