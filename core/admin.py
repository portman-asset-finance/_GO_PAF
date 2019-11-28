from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect

import datetime
from datetime import timedelta

from import_export.admin import ImportExportActionModelAdmin, ImportExportModelAdmin

from .functions_ncf_excel_upload import app_process_props_files, \
                        app_process_settled_agreements, \
                        app_process_advance_payments, \
                        app_process_title_payments, \
                        app_process_arrears_collected, \
                        app_global_terminations

from .functions_bacs_file_process import app_process_bacs_files
from .functions_datacash import app_process_datacash_drawdowns, app_process_datacash_setups
from .functions_bounce_day import app_process_bounce_days

from .models import ncf_bacs_files_to_process, \
                    ncf_bacs_files_processed, \
                    ncf_auddis_addacs_advices, \
                    ncf_udd_advices, \
                    ncf_props_and_payouts, \
                    ncf_settled_agreements, \
                    ncf_advanced_payments, \
                    ncf_arrears_collected, \
                    ncf_agreement_titles, \
                    ncf_global_terminations, \
                    ncf_datacash_drawdowns, \
                    ncf_datacash_setups, \
                    ncf_bacs_reasons, \
                    ncf_dd_call_arrears, \
                    ncf_dd_call_rejections, \
                    ncf_collection_agents, \
                    ncf_arrears_status, \
                    ncf_arrears_summary, \
                    ncf_dd_schedule, \
                    go_extensions, \
                    ncf_ddic_advices, \
                    ncf_bacs_ddic_reasons


# Apellio application configuration and management
@admin.register(go_extensions)
class go_extensions_Admin(admin.ModelAdmin):

    list_display = ['ap_extension_code',
                    'ap_extension_sequence',
                    'ap_extension_description',
                    'ap_extension_required_interface_frequency_days',
                    'ap_extension_last_interface_run',
                    'ap_extension_next_interface_run',
                    'ap_extension_active',
                    ]
    list_per_page = 50

# BACS File Processing
@admin.register(ncf_bacs_files_to_process)
class ncf_bacs_files_to_process_Admin(admin.ModelAdmin):

    change_list_template = "entities/process_bacs_files.html"

    list_display = ['file_identifier',
                    'file_type',
                    'target_data_format',
                    'network_path_source',
                    'network_path_archive',
                    ]
    list_per_page = 20

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('process_bacs_files/', self.process_bacs_files),
        ]
        return my_urls + urls

    def process_bacs_files(self, request):

        app_process_bacs_files()
        self.message_user(request, 'BACS AUDDIS/ADDACS Advices Updated')
        self.message_user(request, 'BACS UDD Advices Updated')

        apellio_extension = go_extensions.objects.get(ap_extension_code='audrun')
        apellio_extension.ap_extension_last_interface_run = datetime.datetime.now()
        apellio_extension.ap_extension_next_interface_run = \
            apellio_extension.ap_extension_last_interface_run + \
            timedelta(days=apellio_extension.ap_extension_required_interface_frequency_days)
        apellio_extension.save()

        return HttpResponseRedirect("../")


@admin.register(ncf_bacs_reasons)
class ncf_bacs_reasons_Admin(admin.ModelAdmin):

    list_display = ['reason_code',
                    'reason_description',
                    ]
    list_per_page = 50


@admin.register(ncf_bacs_ddic_reasons)
class ncf_bacs_ddic_reasons_Admin(admin.ModelAdmin):

    list_display = ['ddic_reason_code',
                    'ddic_reason_description',
                    ]
    list_per_page = 50


@admin.register(ncf_bacs_files_processed)
class ncf_bacs_files_processed_Admin(admin.ModelAdmin):

    list_display = ['file_name',
                    'created_at',
                    ]
    list_per_page = 50
    ordering = ('-created_at',)


@admin.register(ncf_auddis_addacs_advices)
class ncf_auddis_addacs_advices_Admin(admin.ModelAdmin):

    list_display = ['agreement_id',
                    'dd_reference',
                    'dd_payer_name',
                    'dd_reason_code',
                    'dd_reason',
                    'dd_payer_sort_code',
                    'dd_payer_account_number',
                    'dd_payer_new_sort_code',
                    'dd_payer_new_account_number',
                    'dd_effective_date',
                    'dd_due_date',
                    'created_at'
                    ]
    list_per_page = 50
    ordering = ('-dd_effective_date', 'agreement_id', 'dd_reference',)


@admin.register(ncf_udd_advices)
class ncf_udd_advices_Admin(ImportExportActionModelAdmin):

    list_display = ['agreement_id',
                    'dd_reference',
                    'dd_original_process_date',
                    'dd_transcode',
                    'dd_currency',
                    'dd_value',
                    'dd_return_description',
                    'created_at'
                    ]
    list_per_page = 50
    ordering = ('-created_at', '-dd_original_process_date', 'agreement_id', 'dd_reference',)
    date_hierarchy = 'created_at'

    def get_actions(self, request):
        actions = super(ncf_udd_advices_Admin, self).get_actions(request)
        # if 'delete_selected' in actions:
        #     del actions['delete_selected']
        return actions


@admin.register(ncf_ddic_advices)
class ncf_ddic_advices_Admin(admin.ModelAdmin):

    list_display = ['agreement_id',
                    'ddic_SUReference',
                    'ddic_seqno',
                    'ddic_DDIC_Type',
                    'ddic_DateOfDocumentDebit',
                    'ddic_Reason',
                    'ddic_DateOfOriginalDD',
                    'ddic_OriginalDDAmount',
                    'created_at'
                    ]
    list_per_page = 50
    ordering = ('-created_at', 'agreement_id', 'ddic_SUReference', 'ddic_seqno')


# NCF Excel Uploads
@admin.register(ncf_props_and_payouts)
class ncf_props_and_payouts_Admin(admin.ModelAdmin):

    change_list_template = "entities/process_props_files.html"

    list_display = ['agreement_id',
                    'customer_name',
                    'regulated_flag',
                    'agreement_type',
                    'payout_date',
                    'sales_person',
                    'first_rental_date',
                    'final_rental_date',
                    'net_invoice_amount'
                    ]
    list_per_page = 50
    ordering = ('-payout_date',)

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('process_props_files/', self.process_props_files),
        ]
        return my_urls + urls

    def process_props_files(self, request):

        app_process_props_files()
        self.message_user(request, 'Props & Payouts Upload Completed')

        app_process_advance_payments()
        self.message_user(request, 'Advance Payments Upload Completed')

        app_process_arrears_collected()
        self.message_user(request, 'Arrears Collected Upload Completed')

        app_process_settled_agreements()
        self.message_user(request, 'Settled Agreements Upload Completed')

        app_process_title_payments()
        self.message_user(request, 'Gone to Title Upload Completed')

        app_global_terminations()
        self.message_user(request, 'Global Terminations Upload Completed')

        # TODO: PAF Changes - Start
        # TODO: apellio_extension = apellio_extensions.objects.get(ap_extension_code='ncf')
        apellio_extension = apellio_extensions.objects.get(ap_extension_code='paf')
        # PAF Changes - End
        apellio_extension.ap_extension_last_interface_run = datetime.datetime.now()
        apellio_extension.ap_extension_next_interface_run =\
                                apellio_extension.ap_extension_last_interface_run +\
                                timedelta(days=apellio_extension.ap_extension_required_interface_frequency_days)
        apellio_extension.save()

        return HttpResponseRedirect("../")


@admin.register(ncf_advanced_payments)
class ncf_advanced_payments_Admin(admin.ModelAdmin):

    list_display = ['agreement_id',
                    'agreement_name',
                    'advance_value',
                    'method',
                    'advance_date',
                    'notes',
                    ]
    list_per_page = 50
    ordering = ('-advance_date',)


@admin.register(ncf_arrears_collected)
class ncf_arrears_collected_Admin(admin.ModelAdmin):

    list_display = ['ac_collected_date',
                    'ac_agreement_id',
                    'ac_agreement_name',
                    'ac_arrears_collected',
                    'ac_method',
                    'ac_fees_collected',
                    'ac_agent_name',
                    'ac_notes'
                    ]
    list_per_page = 50
    ordering = ('-ac_collected_date',)


@admin.register(ncf_settled_agreements)
class ncf_settled_agreements_Admin(admin.ModelAdmin):

    list_display = ['agreement_id',
                    'agreement_name',
                    'settlement_value',
                    'method',
                    'settlement_date',
                    'notes',
                    'received_from',
                    'agreement_type',
                    'vat_status',
                    'removed_from_sentinel',
                    ]
    list_per_page = 50
    ordering = ('-settlement_date',)


@admin.register(ncf_agreement_titles)
class ncf_agreement_titles_Admin(admin.ModelAdmin):

    list_display = ['agreement_id',
                    'title_date',
                    'invoice_number',
                    'customer_name',
                    'amount_paid',
                    'paying_value',
                    ]
    list_per_page = 50
    ordering = ('-title_date',)


@admin.register(ncf_global_terminations)
class ncf_global_terminations_Admin(admin.ModelAdmin):

    list_display = ['agreement_id',
                    'agreement_name',
                    'agreement_rep',
                    'written_off',
                    'date_terminated',
                    'reason'
                    ]
    list_per_page = 50
    ordering = ('-date_terminated',)


# DataCash Processing
@admin.register(ncf_datacash_drawdowns)
class ncf_datacash_drawdowns_Admin(admin.ModelAdmin):
    change_list_template = "entities/datacash_drawdowns.html"

    list_display = ['agreement_id',
                    'dd_reference',
                    'dd_setup_no',
                    'dd_amount',
                    'dd_method',
                    'dd_request_date',
                    'dd_batch_status',
                    'dd_due_date',
                    'dd_response',
                    'dd_stage',
                    'dd_bacs_reason'
                    ]
    list_per_page = 50
    ordering = ('-dd_request_date', 'agreement_id',)

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('process_datacash_drawdowns/', self.datacash_drawdowns),
        ]
        return my_urls + urls

    def datacash_drawdowns(self, request):

        app_process_datacash_drawdowns()
        self.message_user(request, 'DataCash Drawdowns Updated')

        apellio_extension = go_extensions.objects.get(ap_extension_code='dc_drawdn')
        apellio_extension.ap_extension_last_interface_run = datetime.datetime.now()
        apellio_extension.ap_extension_next_interface_run = \
            apellio_extension.ap_extension_last_interface_run + \
            timedelta(days=apellio_extension.ap_extension_required_interface_frequency_days)
        apellio_extension.save()

        return HttpResponseRedirect("../")


@admin.register(ncf_datacash_setups)
class ncf_datacash_setups_Admin(admin.ModelAdmin):
    change_list_template = "entities/datacash_setups.html"

    list_display = ['agreement_id',
                    'dd_reference',
                    'dd_account_name',
                    'dd_stage',
                    'dd_method',
                    'dd_request_date',
                    'dd_batch_status'
                    ]
    list_per_page = 50
    ordering = ('-dd_request_date', 'agreement_id',)

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('process_datacash_setups/', self.datacash_setups),
        ]
        return my_urls + urls

    def datacash_setups(self, request):
        app_process_datacash_setups()
        self.message_user(request, 'DataCash Setups Updated')

        return HttpResponseRedirect("../")


# Bounce Day Processing
@admin.register(ncf_dd_schedule)
class ncf_dd_schedule_Admin(admin.ModelAdmin):

    change_list_template = "entities/ddcallcontrol.html"

    list_display = ['dd_calendar_due_date',
                    'dd_working_due_date',
                    'dd_call_date',
                    'dd_change_cutoff_date',
                    'dd_status_id',
                    'dd_firstbounce_processed',
                    'dd_process_date01',
                    'dd_process_date02',
                    'dd_bounce_date01',
                    'dd_bounce_date02'
                    ]
    list_per_page = 50
    ordering = ('-dd_status_id','dd_calendar_due_date',)

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('ddcallcontrol/', self.ddcallcontrol),
        ]
        return my_urls + urls

    def ddcallcontrol(self, request):

        app_process_bounce_days()

        self.message_user(request, 'Bounce Day Arrears Updated')
        self.message_user(request, 'Bounce Day DD Cancellations Updated')
        self.message_user(request, 'Arrears and Collections Updated')

        return HttpResponseRedirect("../")


@admin.register(ncf_dd_call_arrears)
class ncf_dd_call_arrears_Admin(ImportExportModelAdmin):

    list_display = ['ar_agreement_id',
                    'ar_account_name',
                    'ar_salesperson',
                    'ar_arrears_rental',
                    'ar_arrears_fee',
                    'ar_arrears_total',
                    'ar_term',
                    'ar_date',
                    'ar_days',
                    'ar_notes',
                    'ar_agent_id',
                    'ar_agreement_phase',
                    'ar_exclude_reason',
                    'ar_dd_original_value',
                    'ar_schedule_value'
                    ]
    list_per_page = 50
    ordering = ('ar_agreement_id',)


@admin.register(ncf_dd_call_rejections)
class ncf_dd_call_rejections_Admin(ImportExportModelAdmin):
    list_display = ['ar_agreement_id',
                    'ar_account_name',
                    'ar_salesperson',
                    'ar_date_cancelled',
                    'ar_term',
                    'ar_reason_cancelled',
                    'ar_days_cancelled',
                    'ar_next_dd_due',
                    'ar_days_until_dd',
                    'ar_notes',
                    'ar_agent_id',
                    'ar_agreement_phase',
                    'ar_exclude_reason',
                    'ar_dd_original_value',
                    'ar_schedule_value'
                    ]
    list_per_page = 50
    ordering = ('ar_agreement_id',)


@admin.register(ncf_collection_agents)
class ncf_collection_agents_Admin(admin.ModelAdmin):

    list_display = ['bd_collection_agent',
                    'bd_agent_primary_manager',
                    'bd_agent_primary_active',
                    'bd_agent_secondary_manager',
                    'bd_agent_secondary_active'
                    ]
    list_per_page = 50
    ordering = ('bd_collection_agent',)


@admin.register(ncf_arrears_status)
class ncf_arrears_status_Admin(admin.ModelAdmin):

    list_display = [
        'col_status_code' ,
        'col_status_description'
    ]


@admin.register(ncf_arrears_summary)
class ncf_arrears_summary_Admin(admin.ModelAdmin):

    list_display = [
        'col_agreement_id',
        'col_agent_id' ,
        'col_arrears_gross_rental' ,
        'col_arrears_gross_fee',
        'col_arrears_gross_total',
        'col_arrears_startdate' ,
        'col_arrears_latestdate',
        'col_arrears_sum_status'
    ]















