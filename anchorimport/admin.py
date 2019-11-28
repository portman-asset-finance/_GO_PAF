from django.contrib import admin

from .models import AnchorimportAgreementDefinitions, \
                    AnchorimportAgreements, \
                    AnchorimportCustomers, \
                    AnchorimportFeeDefinitions, \
                    AnchorimportPaymentProfiles, \
                    AnchorimportTransactionTable, \
                    AnchorimportTransactionTypes


# Register your models here.
@admin.register(AnchorimportAgreementDefinitions)
class AnchorimportAgreementDefinitions_Admin(admin.ModelAdmin):
    list_per_page = 50


@admin.register(AnchorimportAgreements)
class AnchorimportAgreements_Admin(admin.ModelAdmin):
    list_per_page = 50


@admin.register(AnchorimportCustomers)
class AnchorimportCustomers_Admin(admin.ModelAdmin):
    list_per_page = 50


@admin.register(AnchorimportFeeDefinitions)
class AnchorimportFeeDefinitions_Admin(admin.ModelAdmin):
    list_per_page = 50


@admin.register(AnchorimportPaymentProfiles)
class AnchorimportPaymentProfiles_Admin(admin.ModelAdmin):
    list_per_page = 50


@admin.register(AnchorimportTransactionTable)
class AnchorimportTransactionTable_Admin(admin.ModelAdmin):
    list_per_page = 50


@admin.register(AnchorimportTransactionTypes)
class AnchorimportTransactionTypes_Admin(admin.ModelAdmin):
    list_per_page = 50