from django.contrib import admin


from .models import go_customers, go_agreement_definitions, go_agreement_querydetail, \
                    go_account_transaction_summary, go_account_transaction_detail, go_agreements, go_broker,\
                    go_agreement_id_definitions, go_sales_authority, go_funder


admin.site.register(go_broker)
admin.site.register(go_customers)
admin.site.register(go_agreements)

@admin.register(go_sales_authority)
class go_sales_authority_Admin(admin.ModelAdmin):

    list_display = ['full_name',
                    'user',
                    'selectable',
                    ]
    list_per_page = 50

admin.site.register(go_agreement_definitions)
admin.site.register(go_agreement_querydetail)
admin.site.register(go_agreement_id_definitions)
admin.site.register(go_account_transaction_detail)
admin.site.register(go_account_transaction_summary)
admin.site.register(go_funder)