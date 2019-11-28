from django.db import models
from django.contrib.auth.models import User


class go_sales_authority(models.Model):

    full_name = models.CharField(db_column='full_name', max_length=50)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    selectable = models.NullBooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class go_agreement_index(models.Model):

    # go_id = models.CharField(max_length=50, unique=True, null=True)
    # agreement_id = models.CharField(max_length=10, unique=True, null=True)
    # # profile = models.ForeignKey('go_profile_types', null=True, on_delete=models.DO_NOTHING)
    # broker = models.ForeignKey('go_broker', null=True, on_delete=models.DO_NOTHING)
    # funder = models.ForeignKey('go_funder', null=True, on_delete=models.DO_NOTHING)
    # # agreenent_type = models.ForeignKey('go_agreement_definitions', null=True, on_delete=models.DO_NOTHING)
    # agreement_type = models.CharField(max_length=250, null=True)

    go_id = models.CharField(max_length=50, unique=True, null=True)
    agreement_id = models.CharField(max_length=10, unique=True, null=True)
    profile = models.ForeignKey('go_profile_types', null=True, on_delete=models.DO_NOTHING)
    broker = models.ForeignKey('go_broker', null=True, on_delete=models.DO_NOTHING)
    funder = models.ForeignKey('go_funder', null=True, on_delete=models.DO_NOTHING)

    company_ref_no = models.CharField(max_length=250, null=True)
    social_media1 = models.CharField(max_length=250, null=True)
    social_media2 = models.CharField(max_length=250, null=True)
    social_media3 = models.CharField(max_length=250, null=True)

    user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    term = models.IntegerField(null=True)

    agreement_doc_fee = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    agreement_instalment_gross = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    agreement_total_fees = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    agreement_payable_net = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    agreement_payable_gross = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)

    agreement_risk_fee = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    agreement_bamf_fee = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)

    agreement_origin_flag = models.CharField(max_length=250, null=True)
    guarantor1name = models.CharField(max_length=250, null=True)
    agreement_closed_reason = models.CharField(max_length=250, null=True)
    consolidation_info = models.CharField(max_length=250, null=True)
    risk_flag = models.SmallIntegerField(blank=True, null=True)
    bamf_flag = models.SmallIntegerField(blank=True, null=True)
    secondary_flag = models.SmallIntegerField(blank=True, null=True)
    title_flag = models.SmallIntegerField(blank=True, null=True)
    security_flag = models.SmallIntegerField(blank=True, null=True)
    amf_flag = models.SmallIntegerField(blank=True, null=True)
    # TODO: GO#110 - Start
    doc_flag = models.SmallIntegerField(blank=True, null=True)
    # TODO: GO#110 - End

    manual_payments = models.SmallIntegerField(blank=True, null=True, default=0)

    settled_date = models.DateTimeField(blank=True, null=True)
    consolidated_date = models.DateTimeField(blank=True, null=True)
    globalled_date = models.DateTimeField(blank=True, null=True)

    agreement_status = models.CharField(max_length=250, blank=True, null=True)
    companies_house_status_flag = models.CharField(max_length=250, blank=True, null=True)
    # TODO: PAF Changes - Start
    agreement_structure_upfront = models.SmallIntegerField(blank=True, null=True)
    agreement_structure_rentals = models.SmallIntegerField(blank=True, null=True)
    agreement_delay_vat_until = models.SmallIntegerField(blank=True, null=True)
    # TODO: PAF Changes - End

    # end_of_life_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.agreement_id)


class go_agreements(models.Model):

    go_id = models.OneToOneField('go_agreement_index', max_length=50, unique=True, null=True, on_delete=models.DO_NOTHING)

    agreementnumber = models.CharField(db_column='AgreementNumber', max_length=10, unique=True, default='')  # Field name made lowercase.
    agreementcustomernumber = models.ForeignKey('go_customers',db_column='AgreementCustomerNumber',
                                                max_length=10, blank=True, null=True, to_field="customernumber", on_delete=models.CASCADE)  # Field name made lowercase.
    agreementcreator = models.CharField(db_column='AgreementCreator', max_length=15, blank=True, null=True)  # Field name made lowercase.
    agreementamendor = models.CharField(db_column='AgreementAmendor', max_length=15, blank=True, null=True)  # Field name made lowercase.
    agreementborrowers = models.CharField(db_column='AgreementBorrowers', max_length=110, blank=True, null=True)  # Field name made lowercase.
    agreementguarantors = models.CharField(db_column='AgreementGuarantors', max_length=110, blank=True, null=True)  # Field name made lowercase.
    agreementdefaultcode = models.CharField(db_column='AgreementDefaultCode', max_length=2, blank=True, null=True)  # Field name made lowercase.
    agreementinfolinkoveride = models.CharField(db_column='AgreementInfoLinkOveride', max_length=1, blank=True, null=True)  # Field name made lowercase.
    agreementstatusoveride = models.CharField(db_column='AgreementStatusOveride', max_length=1, blank=True, null=True)  # Field name made lowercase.
    agreementspecialinstruction = models.CharField(db_column='AgreementSpecialInstruction', max_length=1, blank=True, null=True)  # Field name made lowercase.
    agreementnameaddresschange = models.CharField(db_column='AgreementNameAddressChange', max_length=1, blank=True, null=True)  # Field name made lowercase.
    agreementcaisflagsetting = models.CharField(db_column='AgreementCAISFlagSetting', max_length=1, blank=True, null=True)  # Field name made lowercase.
    agreementinvoicenumber = models.CharField(db_column='AgreementInvoiceNumber', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementnextnumber = models.CharField(db_column='AgreementNextNumber', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementanalysiscode = models.CharField(db_column='AgreementAnalysisCode', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementbranch = models.CharField(db_column='AgreementBranch', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementassessofficer = models.CharField(db_column='AgreementAssessOfficer', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementretailoutlet = models.CharField(db_column='AgreementRetailOutlet', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementauthority = models.CharField(db_column='AgreementAuthority', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementmiscellaneous = models.CharField(db_column='AgreementMiscellaneous', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementsalessource = models.CharField(db_column='AgreementSalesSource', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementsalesmannumber = models.CharField(db_column='AgreementSalesmanNumber', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementdealernumber = models.CharField(db_column='AgreementDealerNumber', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementpersonnumber = models.CharField(db_column='AgreementPersonNumber', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementbankaccountname = models.CharField(db_column='AgreementBankAccountName', max_length=20, blank=True, null=True)  # Field name made lowercase.
    agreementbanksortcode = models.CharField(db_column='AgreementBankSortCode', max_length=15, blank=True, null=True)  # Field name made lowercase.
    agreementbankaccountnumber = models.CharField(db_column='AgreementBankAccountNumber', max_length=15, blank=True, null=True)  # Field name made lowercase.
    agreementbankreference = models.CharField(db_column='AgreementBankReference', max_length=20, blank=True, null=True)  # Field name made lowercase.
    agreementbankaccounttype = models.CharField(db_column='AgreementBankAccountType', max_length=1, blank=True, null=True)  # Field name made lowercase.
    agreementbanktranscode = models.CharField(db_column='AgreementBankTransCode', max_length=2, blank=True, null=True)  # Field name made lowercase.
    agreementstatus = models.CharField(db_column='AgreementStatus', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementintroducer = models.CharField(db_column='AgreementIntroducer', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementautostatus = models.CharField(db_column='AgreementAutoStatus', max_length=20, blank=True, null=True)  # Field name made lowercase.
    agreementarrearsstatus = models.CharField(db_column='AgreementArrearsStatus', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementnumberold = models.CharField(db_column='AgreementNumberOld', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementsiccode = models.CharField(db_column='AgreementSICCode', max_length=20, blank=True, null=True)  # Field name made lowercase.
    agreementsiccodedesc = models.CharField(db_column='AgreementSICCodeDesc', max_length=100, blank=True, null=True)  # Field name made lowercase.
    agreementintrrateid = models.CharField(db_column='AgreementIntrRateID', max_length=8, blank=True, null=True)  # Field name made lowercase.
    agreementexternalreferenceno = models.CharField(db_column='AgreementExternalReferenceNo', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementexternalreferenceno2 = models.CharField(db_column='AgreementExternalReferenceNo2', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementexternalreferenceno3 = models.CharField(db_column='AgreementExternalReferenceNo3', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementdepotnumber = models.CharField(db_column='AgreementDepotNumber', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementpurpose = models.CharField(db_column='AgreementPurpose', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementbaddebtstatus = models.CharField(db_column='AgreementBadDebtStatus', max_length=2, blank=True, null=True)  # Field name made lowercase.
    agreementdatacashmerchantref = models.CharField(db_column='AgreementDataCashMerchantRef', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementprincipal = models.DecimalField(db_column='AgreementPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementoriginalprincipal = models.DecimalField(db_column='AgreementOriginalPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementcharges = models.DecimalField(db_column='AgreementCharges', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalcostsprincipal = models.DecimalField(db_column='AgreementTotalCostsPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalcostsinterest = models.DecimalField(db_column='AgreementTotalCostsInterest', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdepositcash = models.DecimalField(db_column='AgreementDepositCash', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdepositpartex = models.DecimalField(db_column='AgreementDepositPartEx', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdealercommission = models.DecimalField(db_column='AgreementDealerCommission', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdealercommissionvat = models.DecimalField(db_column='AgreementDealerCommissionVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdealercommissioninsr = models.DecimalField(db_column='AgreementDealerCommissionInsr', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementapr = models.DecimalField(db_column='AgreementAPR', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementextrainterest = models.DecimalField(db_column='AgreementExtraInterest', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalrebates = models.DecimalField(db_column='AgreementTotalRebates', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalwoffprincipal = models.DecimalField(db_column='AgreementTotalWOffPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalwoffinterest = models.DecimalField(db_column='AgreementTotalWOffInterest', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementextraprincipal = models.DecimalField(db_column='AgreementExtraPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementoriginalinterest = models.DecimalField(db_column='AgreementOriginalInterest', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalprincipalpaid = models.DecimalField(db_column='AgreementTotalPrincipalPaid', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalinterestpaid = models.DecimalField(db_column='AgreementTotalInterestPaid', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalprincipalpaidtm = models.DecimalField(db_column='AgreementTotalPrincipalPaidTM', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalinterestpaidtm = models.DecimalField(db_column='AgreementTotalInterestPaidTM', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementarrearsnetprincipal = models.DecimalField(db_column='AgreementArrearsNETPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementarrearsnetinterest = models.DecimalField(db_column='AgreementArrearsNETInterest', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalarrearsnet = models.DecimalField(db_column='AgreementTotalArrearsNET', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalarrearsnetfee = models.DecimalField(db_column='AgreementTotalArrearsNETFee', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalarrearsvatfee = models.DecimalField(db_column='AgreementTotalArrearsVatFee', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementresidualnet = models.DecimalField(db_column='AgreementResidualNET', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementinstalmentnet = models.DecimalField(db_column='AgreementInstalmentNET', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementcurrentbalancenet = models.DecimalField(db_column='AgreementCurrentBalanceNET', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementadvanceinstalmentnet = models.DecimalField(db_column='AgreementAdvanceInstalmentNET', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementinputvat = models.DecimalField(db_column='AgreementInputVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementoutputvat = models.DecimalField(db_column='AgreementOutputVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementresidualvat = models.DecimalField(db_column='AgreementResidualVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementadvanceinstalmentvat = models.DecimalField(db_column='AgreementAdvanceInstalmentVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementarrearsvat = models.DecimalField(db_column='AgreementArrearsVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalpaidvat = models.DecimalField(db_column='AgreementTotalPaidVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementinstalmentvat = models.DecimalField(db_column='AgreementInstalmentVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtaxdeductable = models.DecimalField(db_column='AgreementTAXDeductable', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtaxpercentage = models.DecimalField(db_column='AgreementTAXPercentage', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementarrearstax = models.DecimalField(db_column='AgreementArrearsTAX', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdebitinterest = models.DecimalField(db_column='AgreementDebitInterest', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementextraintrpaid = models.DecimalField(db_column='AgreementExtraIntrPaid', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalcostspaid = models.DecimalField(db_column='AgreementTotalCostsPaid', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalcharges = models.DecimalField(db_column='AgreementTotalCharges', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalins = models.DecimalField(db_column='AgreementTotalIns', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalfees = models.DecimalField(db_column='AgreementTotalFees', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementarrearstotalins = models.DecimalField(db_column='AgreementArrearsTotalINS', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementinstalmentins = models.DecimalField(db_column='AgreementInstalmentINS', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementcurrentbalanceins = models.DecimalField(db_column='AgreementCurrentBalanceINS', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdebitintruplift = models.DecimalField(db_column='AgreementDebitIntrUpLift', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefaultbalance = models.DecimalField(db_column='AgreementDefaultBalance', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementexparrangement = models.DecimalField(db_column='AgreementExpArrangement', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementcapitalallowance = models.DecimalField(db_column='AgreementCapitalAllowance', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementtotalprincipal = models.DecimalField(db_column='AgreementTotalPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementadditionalirrfee = models.DecimalField(db_column='AgreementAdditionalIRRFee', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementcreditlimit = models.DecimalField(db_column='AgreementCreditLimit', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementinsuranceapr = models.DecimalField(db_column='AgreementInsuranceAPR', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementintronlymnths = models.DecimalField(db_column='AgreementIntrOnlyMnths', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementgoodsdiscountrate = models.DecimalField(db_column='AgreementGoodsDiscountRate', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementbaseprincipal = models.DecimalField(db_column='AgreementBasePrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementinvoicediscountrate = models.DecimalField(db_column='AgreementInvoiceDiscountRate', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementearlyddpayment = models.DecimalField(db_column='AgreementEarlyDDPayment', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementfhbr = models.DecimalField(db_column='AgreementFHBR', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementbrokerfee = models.DecimalField(db_column='AgreementBrokerFee', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementintrratevalue = models.DecimalField(db_column='AgreementIntrRateValue', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementsubsidy = models.DecimalField(db_column='AgreementSubsidy', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementnetyield = models.DecimalField(db_column='AgreementNetYield', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementgrossyield = models.DecimalField(db_column='AgreementGrossYield', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementaccruedinterest = models.DecimalField(db_column='AgreementAccruedInterest', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementsubsidy2 = models.DecimalField(db_column='AgreementSubsidy2', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementbrokercommission = models.DecimalField(db_column='AgreementBrokerCommission', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementbrokercommissionvat = models.DecimalField(db_column='AgreementBrokerCommissionVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementsalesmancommission = models.DecimalField(db_column='AgreementSalesmanCommission', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementaprfee = models.DecimalField(db_column='AgreementAPRFee', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementbaddebtprovision = models.DecimalField(db_column='AgreementBadDebtProvision', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementaprnet = models.DecimalField(db_column='AgreementAPRNet', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementbaddebtpercentage = models.DecimalField(db_column='AgreementBadDebtPercentage', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementrefixaddamount = models.DecimalField(db_column='AgreementRefixAddAmount', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementagreementdate = models.DateTimeField(db_column='AgreementAgreementDate', blank=True, null=True)  # Field name made lowercase.
    agreementfirstpaymentdate = models.DateTimeField(db_column='AgreementFirstPaymentDate', blank=True, null=True)  # Field name made lowercase.
    agreementupfrontdate = models.DateTimeField(db_column='AgreementUpfrontDate', blank=True, null=True)  # Field name made lowercase.
    agreementresidualdate = models.DateTimeField(db_column='AgreementResidualDate', blank=True, null=True)  # Field name made lowercase.
    agreementstatementdate = models.DateTimeField(db_column='AgreementStatementDate', blank=True, null=True)  # Field name made lowercase.
    agreementcreatedate = models.DateTimeField(db_column='AgreementCreateDate', blank=True, null=True)  # Field name made lowercase.
    agreementamenddate = models.DateTimeField(db_column='AgreementAmendDate', blank=True, null=True)  # Field name made lowercase.
    agreementsettleddate = models.DateTimeField(db_column='AgreementSettledDate', blank=True, null=True)  # Field name made lowercase.
    agreementlastduedate = models.DateTimeField(db_column='AgreementLastDueDate', blank=True, null=True)  # Field name made lowercase.
    agreementnextduedate = models.DateTimeField(db_column='AgreementNextDueDate', blank=True, null=True)  # Field name made lowercase.
    agreementintrstartdate = models.DateTimeField(db_column='AgreementIntrStartDate', blank=True, null=True)  # Field name made lowercase.
    agreementdefaultdate = models.DateTimeField(db_column='AgreementDefaultDate', blank=True, null=True)  # Field name made lowercase.
    agreementnumberchangeexperiandate = models.DateTimeField(db_column='AgreementNumberChangeExperianDate', blank=True, null=True)  # Field name made lowercase.
    agreementnumberchangeequifaxdate = models.DateTimeField(db_column='AgreementNumberChangeEquifaxDate', blank=True, null=True)  # Field name made lowercase.
    agreementearlydddate = models.DateTimeField(db_column='AgreementEarlyDDDate', blank=True, null=True)  # Field name made lowercase.
    agreementintrratedateset = models.DateTimeField(db_column='AgreementIntrRateDateSet', blank=True, null=True)  # Field name made lowercase.
    agreementintrraterefixdate = models.DateTimeField(db_column='AgreementIntrRateRefixDate', blank=True, null=True)  # Field name made lowercase.
    agreementexperiancloseddate = models.DateTimeField(db_column='AgreementExperianClosedDate', blank=True, null=True)  # Field name made lowercase.
    agreementintronlystartdate = models.DateTimeField(db_column='AgreementIntrOnlyStartDate', blank=True, null=True)  # Field name made lowercase.
    agreementnextstatementdate = models.DateTimeField(db_column='AgreementNextStatementDate', blank=True, null=True)  # Field name made lowercase.
    agreementdiscountdate1 = models.DateTimeField(db_column='AgreementDiscountDate1', blank=True, null=True)  # Field name made lowercase.
    agreementdiscountdate2 = models.DateTimeField(db_column='AgreementDiscountDate2', blank=True, null=True)  # Field name made lowercase.
    agreementfrozendate = models.DateTimeField(db_column='AgreementFrozenDate', blank=True, null=True)  # Field name made lowercase.
    agreementbaddebtdate = models.DateTimeField(db_column='AgreementBadDebtDate', blank=True, null=True)  # Field name made lowercase.
    agreementpaymentmethod = models.SmallIntegerField(db_column='AgreementPaymentMethod', blank=True, null=True)  # Field name made lowercase.
    agreementnumpayments = models.SmallIntegerField(db_column='AgreementNumPayments', blank=True, null=True)  # Field name made lowercase.
    agreementupfrontpayments = models.SmallIntegerField(db_column='AgreementUpfrontPayments', blank=True, null=True)  # Field name made lowercase.
    agreementpaymentfrequency = models.SmallIntegerField(db_column='AgreementPaymentFrequency', blank=True, null=True)  # Field name made lowercase.
    agreementpenaltyintrdueday = models.SmallIntegerField(db_column='AgreementPenaltyIntrDueDay', blank=True, null=True)  # Field name made lowercase.
    agreementpenaltyinterestcode = models.SmallIntegerField(db_column='AgreementPenaltyInterestCode', blank=True, null=True)  # Field name made lowercase.
    agreementagreementtypeid = models.ForeignKey('go_agreement_definitions', on_delete=models.CASCADE,
                                                 db_column='AgreementAgreementTypeID', blank=True, null=True, to_field="agreementdefid")  # Field name made lowercase.
    agreementcollectiontype = models.SmallIntegerField(db_column='AgreementCollectionType', blank=True, null=True)  # Field name made lowercase.
    agreementregulated = models.SmallIntegerField(db_column='AgreementRegulated', blank=True, null=True)  # Field name made lowercase.
    agreementfinancecompanycode = models.SmallIntegerField(db_column='AgreementFinanceCompanyCode', blank=True, null=True)  # Field name made lowercase.
    agreementdebitinterestcode = models.SmallIntegerField(db_column='AgreementDebitInterestCode', blank=True, null=True)  # Field name made lowercase.
    agreementhpistatus = models.SmallIntegerField(db_column='AgreementHPIStatus', blank=True, null=True)  # Field name made lowercase.
    agreementdueday = models.SmallIntegerField(db_column='AgreementDueDay', blank=True, null=True)  # Field name made lowercase.
    agreementarrearsletter = models.SmallIntegerField(db_column='AgreementArrearsLetter', blank=True, null=True)  # Field name made lowercase.
    agreementgenericpersontype = models.SmallIntegerField(db_column='AgreementGenericPersonType', blank=True, null=True)  # Field name made lowercase.
    agreementexperianhpistatus = models.SmallIntegerField(db_column='AgreementExperianHPIStatus', blank=True, null=True)  # Field name made lowercase.
    agreementincomeassessment = models.SmallIntegerField(db_column='AgreementIncomeAssessment', blank=True, null=True)  # Field name made lowercase.
    agreementsectionofmonth = models.SmallIntegerField(db_column='AgreementSectionOfMonth', blank=True, null=True)  # Field name made lowercase.
    agreementdayofweek = models.SmallIntegerField(db_column='AgreementDayOfWeek', blank=True, null=True)  # Field name made lowercase.
    agreementautocolldeposit = models.SmallIntegerField(db_column='AgreementAutoCollDeposit', blank=True, null=True)  # Field name made lowercase.
    agreementdiscountrate = models.SmallIntegerField(db_column='AgreementDiscountRate', blank=True, null=True)  # Field name made lowercase.
    agreementproposalid = models.IntegerField(db_column='AgreementProposalID', blank=True, null=True)  # Field name made lowercase.
    agreementsettledflag = models.NullBooleanField(db_column='AgreementSettledFlag', blank=True, null=True)  # Field name made lowercase.
    agreementseasonalpayments = models.NullBooleanField(db_column='AgreementSeasonalPayments', blank=True, null=True)  # Field name made lowercase.
    agreementarrearsfrozen = models.NullBooleanField(db_column='AgreementArrearsFrozen', blank=True, null=True)  # Field name made lowercase.
    agreementletterprinted = models.NullBooleanField(db_column='AgreementLetterPrinted', blank=True, null=True)  # Field name made lowercase.
    agreementposted = models.NullBooleanField(db_column='AgreementPosted', blank=True, null=True)  # Field name made lowercase.
    agreementignoreletter = models.NullBooleanField(db_column='AgreementIgnoreLetter', blank=True, null=True)  # Field name made lowercase.
    agreementuserecurringins = models.NullBooleanField(db_column='AgreementUseRecurringIns', blank=True, null=True)  # Field name made lowercase.
    agreementpayoutcomplete = models.NullBooleanField(db_column='AgreementPayoutComplete', blank=True, null=True)  # Field name made lowercase.
    agreementintrratelocked = models.NullBooleanField(db_column='AgreementIntrRateLocked', blank=True, null=True)  # Field name made lowercase.
    agreementautocpdone = models.NullBooleanField(db_column='AgreementAutoCPDone', blank=True, null=True)  # Field name made lowercase.
    agreementexperianclosed = models.NullBooleanField(db_column='AgreementExperianClosed', blank=True, null=True)  # Field name made lowercase.
    agreementautocollectintronly = models.NullBooleanField(db_column='AgreementAutoCollectIntrOnly', blank=True, null=True)  # Field name made lowercase.
    agreementexported = models.NullBooleanField(db_column='AgreementExported', blank=True, null=True)  # Field name made lowercase.
    agreementmanualintervention = models.NullBooleanField(db_column='AgreementManualIntervention', blank=True, null=True)  # Field name made lowercase.
    agreementmonthlyinvoice = models.NullBooleanField(db_column='AgreementMonthlyInvoice', blank=True, null=True)  # Field name made lowercase.
    agreementexportexclude = models.NullBooleanField(db_column='AgreementExportExclude', blank=True, null=True)  # Field name made lowercase.
    agreementupfrontautocollected = models.NullBooleanField(db_column='AgreementUpfrontAutoCollected', blank=True, null=True)  # Field name made lowercase.
    agreementstoppenaltyintr = models.NullBooleanField(db_column='AgreementStopPenaltyIntr', blank=True, null=True)  # Field name made lowercase.
    agreementnoinvoice = models.NullBooleanField(db_column='AgreementNoInvoice', blank=True, null=True)  # Field name made lowercase.
    agreementdlrannualfeeignored = models.NullBooleanField(db_column='AgreementDlrAnnualFeeIgnored', blank=True, null=True)  # Field name made lowercase.
    agreementrefixpaylock = models.NullBooleanField(db_column='AgreementRefixPayLock', blank=True, null=True)  # Field name made lowercase.
    agreementpayadvanceio = models.NullBooleanField(db_column='AgreementPayAdvanceIO', blank=True, null=True)  # Field name made lowercase.
    agreementregularpayment = models.NullBooleanField(db_column='AgreementRegularPayment', blank=True, null=True)  # Field name made lowercase.
    agreementccd = models.NullBooleanField(db_column='AgreementCCD', blank=True, null=True)  # Field name made lowercase.
    agreementbaddebtposted = models.NullBooleanField(db_column='AgreementBadDebtPosted', blank=True, null=True)  # Field name made lowercase.
    agreementmemorandum = models.TextField(db_column='AgreementMemorandum', blank=True, null=True)  # Field name made lowercase.
    agreementprevnumber = models.TextField(db_column='AgreementPrevNumber', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementarrearshistory = models.TextField(db_column='AgreementArrearsHistory', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementseasonalmonths = models.TextField(db_column='AgreementSeasonalMonths', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementeir = models.FloatField(db_column='AgreementEIR', blank=True, null=True)  # Field name made lowercase.
    agreementpersoncommission = models.DecimalField(db_column='AgreementPersonCommission', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementpersoncommissionvat = models.DecimalField(db_column='AgreementPersonCommissionVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementsalesmancommissionvat = models.DecimalField(db_column='AgreementSalesmanCommissionVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementwarningflag = models.CharField(db_column='AgreementWarningFlag', max_length=2, blank=True, null=True)  # Field name made lowercase.
    agreementpayouttrantypeid = models.SmallIntegerField(db_column='AgreementPayoutTranTypeID', blank=True, null=True)  # Field name made lowercase.
    agreementwarningtext = models.CharField(db_column='AgreementWarningText', max_length=255, blank=True, null=True)  # Field name made lowercase.
    agreementtransmatchreference = models.CharField(db_column='AgreementTransMatchReference', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementfunderid = models.SmallIntegerField(db_column='AgreementFunderID', blank=True, null=True)  # Field name made lowercase.
    agreementpreviousfunderid = models.SmallIntegerField(db_column='AgreementPreviousFunderID', blank=True, null=True)  # Field name made lowercase.
    agreementcapitalisedcomm = models.DecimalField(db_column='AgreementCapitalisedComm', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementfunderchangereason = models.CharField(db_column='AgreementFunderChangeReason', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementsettlementreason = models.CharField(db_column='AgreementSettlementReason', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementprofitloss = models.DecimalField(db_column='AgreementProfitLoss', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementuseprofitloss = models.NullBooleanField(db_column='AgreementUseProfitLoss', blank=True, null=True)  # Field name made lowercase.
    agreementacpdefaultcustomer = models.CharField(db_column='AgreementACPDefaultCustomer', max_length=4, blank=True, null=True)  # Field name made lowercase.
    agreementnorefund = models.NullBooleanField(db_column='AgreementNoRefund', blank=True, null=True)  # Field name made lowercase.
    agreementdisableccp = models.NullBooleanField(db_column='AgreementDisableCCP', blank=True, null=True)  # Field name made lowercase.
    agreementbankiban = models.CharField(db_column='AgreementBankIBAN', max_length=34, blank=True, null=True)  # Field name made lowercase.
    agreementpenintrmaxdays = models.SmallIntegerField(db_column='AgreementPenIntrMaxDays', blank=True, null=True)  # Field name made lowercase.
    agreementfundingsource = models.CharField(db_column='AgreementFundingSource', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementexternalreferenceno4 = models.CharField(db_column='AgreementExternalReferenceNo4', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementexternalreferenceno5 = models.CharField(db_column='AgreementExternalReferenceNo5', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementaccruedinteresttd = models.DecimalField(db_column='AgreementAccruedInterestTD', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdaysinarrears = models.DecimalField(db_column='AgreementDaysInArrears', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementp2pfeecommmargin = models.DecimalField(db_column='AgreementP2PFeeCommMargin', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementnpvrateuplift = models.DecimalField(db_column='AgreementNPVRateUplift', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementworkingdays = models.SmallIntegerField(db_column='AgreementWorkingDays', blank=True, null=True)  # Field name made lowercase.
    agreementicbsubmitdate = models.DateTimeField(db_column='AgreementICBSubmitDate', blank=True, null=True)  # Field name made lowercase.
    agreementacquisproductcode = models.CharField(db_column='AgreementACQUISProductCode', max_length=7, blank=True, null=True)  # Field name made lowercase.
    agreementletterprinteduser = models.CharField(db_column='AgreementLetterPrintedUser', max_length=25, blank=True, null=True)  # Field name made lowercase.
    agreementpayoutdeferreddate = models.DateTimeField(db_column='AgreementPayoutDeferredDate', blank=True, null=True)  # Field name made lowercase.
    agreementbankbic = models.CharField(db_column='AgreementBankBIC', max_length=11, blank=True, null=True)  # Field name made lowercase.
    agreementgaugescore = models.SmallIntegerField(db_column='AgreementGaugeScore', blank=True, null=True)  # Field name made lowercase.
    agreementsettlementsubreason = models.CharField(db_column='AgreementSettlementSubReason', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementproducttierid = models.IntegerField(db_column='AgreementProductTierID', blank=True, null=True)  # Field name made lowercase.
    agreementexpectedinstalment = models.DecimalField(db_column='AgreementExpectedInstalment', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementcpaconsentrevoked = models.NullBooleanField(db_column='AgreementCPAConsentRevoked', blank=True, null=True)  # Field name made lowercase.
    agreementstopaccrualintr = models.NullBooleanField(db_column='AgreementStopAccrualIntr', blank=True, null=True)  # Field name made lowercase.
    agreementhierarchyrate = models.SmallIntegerField(db_column='AgreementHierarchyRate', blank=True, null=True)  # Field name made lowercase.
    agreementunutilisedcreditrate = models.DecimalField(db_column='AgreementUnutilisedCreditRate', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementrefixaddnper = models.SmallIntegerField(db_column='AgreementRefixAddNPer', blank=True, null=True)  # Field name made lowercase.
    agreementcontractenddate = models.DateTimeField(db_column='AgreementContractEndDate', blank=True, null=True)  # Field name made lowercase.
    agreementaltergoodsagreementnumber = models.CharField(db_column='AgreementAlterGoodsAgreementNumber', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementstopduextracalc = models.NullBooleanField(db_column='AgreementStopDUExtraCalc', blank=True, null=True)  # Field name made lowercase.
    agreementgenericperson7number = models.CharField(db_column='AgreementGenericPerson7Number', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementgenericperson8number = models.CharField(db_column='AgreementGenericPerson8Number', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementgenericperson9number = models.CharField(db_column='AgreementGenericPerson9Number', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementshadowinterestrate = models.DecimalField(db_column='AgreementShadowInterestRate', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementshadowinteresttd = models.DecimalField(db_column='AgreementShadowInterestTD', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    assetfinancenetadvance = models.DecimalField(db_column='AssetFinanceNetAdvance', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    assetfinanceinputvat = models.DecimalField(db_column='AssetFinanceInputVAT', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    assetfinanceinputvrt = models.DecimalField(db_column='AssetFinanceInputVRT', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    assetfinancetotaltaxinput = models.DecimalField(db_column='AssetFinanceTotalTAXInput', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    assetfinancetotalfinancedamount = models.DecimalField(db_column='AssetFinanceTotalFinancedAmount', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    assetfinancetotalassetcost = models.DecimalField(db_column='AssetFinanceTotalAssetCost', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementclosedflag = models.ForeignKey('core.ncf_applicationwide_text', on_delete=models.CASCADE, blank=True, null=True, to_field="app_text_code")


    class Meta:
        verbose_name = 'Go Agreement'
        verbose_name_plural = 'Go Agreements'

    def __str__(self):
        return '{}'.format(self.agreementnumber)


class go_agreement_definitions(models.Model):
    agreementdefid = models.SmallIntegerField(db_column='AgreementDefID', unique=True)  # Field name made lowercase.
    agreementdefname = models.CharField(db_column='AgreementDefName', max_length=200, blank=True, null=True)  # Field name made lowercase.
    agreementdefabbreviation = models.CharField(db_column='AgreementDefAbbreviation', max_length=3, blank=True, null=True)  # Field name made lowercase.
    agreementdeftype = models.SmallIntegerField(db_column='AgreementDefType', blank=True, null=True)  # Field name made lowercase.
    agreementdefcolour = models.SmallIntegerField(db_column='AgreementDefColour', blank=True, null=True)  # Field name made lowercase.
    agreementdefpaymethod = models.CharField(db_column='AgreementDefPayMethod', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdefcollecttype = models.SmallIntegerField(db_column='AgreementDefCollectType', blank=True, null=True)  # Field name made lowercase.
    agreementdefnumberofpayments = models.SmallIntegerField(db_column='AgreementDefNumberOfPayments', blank=True, null=True)  # Field name made lowercase.
    agreementdefpaymentfrequency = models.SmallIntegerField(db_column='AgreementDefPaymentFrequency', blank=True, null=True)  # Field name made lowercase.
    agreementdeffirstpayment = models.SmallIntegerField(db_column='AgreementDefFirstPayment', blank=True, null=True)  # Field name made lowercase.
    agreementdefupfrontpayments = models.SmallIntegerField(db_column='AgreementDefUpfrontPayments', blank=True, null=True)  # Field name made lowercase.
    agreementdefinterestperc = models.DecimalField(db_column='AgreementDefInterestPerc', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefinterestmethod = models.SmallIntegerField(db_column='AgreementDefInterestMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefrebatesexcludeupfronts = models.NullBooleanField(db_column='AgreementDefRebatesExcludeUpfronts', blank=True, null=True)  # Field name made lowercase.
    agreementdefrebatesfees = models.TextField(db_column='AgreementDefRebatesFees', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefrebatesinsurances = models.TextField(db_column='AgreementDefRebatesInsurances', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefappmethod = models.SmallIntegerField(db_column='AgreementDefAppMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefprofilemethod = models.SmallIntegerField(db_column='AgreementDefProfileMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefvat = models.DecimalField(db_column='AgreementDefVat', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefratemethod = models.SmallIntegerField(db_column='AgreementDefRateMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefroundmonthly = models.SmallIntegerField(db_column='AgreementDefRoundMonthly', blank=True, null=True)  # Field name made lowercase.
    agreementdefrounddaily = models.SmallIntegerField(db_column='AgreementDefRoundDaily', blank=True, null=True)  # Field name made lowercase.
    agreementdefroundlastdigit = models.SmallIntegerField(db_column='AgreementDefRoundLastDigit', blank=True, null=True)  # Field name made lowercase.
    agreementdefvatmethod = models.SmallIntegerField(db_column='AgreementDefVatMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefarrsmethod = models.SmallIntegerField(db_column='AgreementDefArrsMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefflatratemethod = models.SmallIntegerField(db_column='AgreementDefFlatRateMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefallowreloans = models.NullBooleanField(db_column='AgreementDefAllowReloans', blank=True, null=True)  # Field name made lowercase.
    agreementdefreloanword = models.CharField(db_column='AgreementDefReloanWord', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdefreloantranstype = models.CharField(db_column='AgreementDefReloanTransType', max_length=100, blank=True, null=True)  # Field name made lowercase.
    agreementdefautoreloan = models.NullBooleanField(db_column='AgreementDefAutoReloan', blank=True, null=True)  # Field name made lowercase.
    agreementdeftax = models.DecimalField(db_column='AgreementDefTax', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdeftaxmethod = models.SmallIntegerField(db_column='AgreementDefTaxMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefregulated = models.SmallIntegerField(db_column='AgreementDefRegulated', blank=True, null=True)  # Field name made lowercase.
    agreementdeflastpaytext = models.CharField(db_column='AgreementDefLastPayText', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdeflastpaynum = models.SmallIntegerField(db_column='AgreementDefLastPayNum', blank=True, null=True)  # Field name made lowercase.
    agreementdefseasonalpayments = models.SmallIntegerField(db_column='AgreementDefSeasonalPayments', blank=True, null=True)  # Field name made lowercase.
    agreementdefautonumprefix = models.CharField(db_column='AgreementDefAutoNumPrefix', max_length=5, blank=True, null=True)  # Field name made lowercase.
    agreementdefautonumincrement = models.IntegerField(db_column='AgreementDefAutoNumIncrement', blank=True, null=True)  # Field name made lowercase.
    agreementdefbasecurrency = models.CharField(db_column='AgreementDefBaseCurrency', max_length=3, blank=True, null=True)  # Field name made lowercase.
    agreementdefusesagecodes = models.NullBooleanField(db_column='AgreementDefUseSageCodes', blank=True, null=True)  # Field name made lowercase.
    agreementdefruleof78addmnths = models.SmallIntegerField(db_column='AgreementDefRuleOf78AddMnths', blank=True, null=True)  # Field name made lowercase.
    agreementdefsecondaryoption = models.SmallIntegerField(db_column='AgreementDefSecondaryOption', blank=True, null=True)  # Field name made lowercase.
    agreementdefsecondarydefpercent = models.DecimalField(db_column='AgreementDefSecondaryDefPercent', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefregulatedoveride = models.DecimalField(db_column='AgreementDefRegulatedOveride', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefregulatedtypes = models.IntegerField(db_column='AgreementDefRegulatedTypes', blank=True, null=True)  # Field name made lowercase.
    agreementdefproratasplit = models.NullBooleanField(db_column='AgreementDefProRataSplit', blank=True, null=True)  # Field name made lowercase.
    agreementdefagreementdate = models.SmallIntegerField(db_column='AgreementDefAgreementDate', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod = models.TextField(db_column='AgreementDefSageMethod', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefsagemethod2 = models.TextField(db_column='AgreementDefSageMethod2', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefignoreplannedmethod = models.NullBooleanField(db_column='AgreementDefIgnorePlannedMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagebatchpost = models.NullBooleanField(db_column='AgreementDefSageBatchPost', blank=True, null=True)  # Field name made lowercase.
    agreementdefvardebitintrfreq = models.SmallIntegerField(db_column='AgreementDefVarDebitIntrFreq', blank=True, null=True)  # Field name made lowercase.
    agreementdefvardebitintrmonth = models.SmallIntegerField(db_column='AgreementDefVarDebitIntrMonth', blank=True, null=True)  # Field name made lowercase.
    agreementdefcalcchargesexcludeupfront = models.NullBooleanField(db_column='AgreementDefCalcChargesExcludeUpfront', blank=True, null=True)  # Field name made lowercase.
    agreementdefvarintronlymnths = models.SmallIntegerField(db_column='AgreementDefVarIntrOnlyMnths', blank=True, null=True)  # Field name made lowercase.
    agreementdefgoodstype = models.SmallIntegerField(db_column='AgreementDefGoodsType', blank=True, null=True)  # Field name made lowercase.
    agreementdefreloanupfrontamount = models.CharField(db_column='AgreementDefReloanUpfrontAmount', max_length=100, blank=True, null=True)  # Field name made lowercase.
    agreementdefreloanuserenewal = models.CharField(db_column='AgreementDefReloanUseRenewal', max_length=100, blank=True, null=True)  # Field name made lowercase.
    agreementdefvarinstalmentmethod = models.SmallIntegerField(db_column='AgreementDefVarInstalmentMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefminimumpayment = models.DecimalField(db_column='AgreementDefMinimumPayment', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefminimumpercentage = models.DecimalField(db_column='AgreementDefMinimumPercentage', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultdueday = models.SmallIntegerField(db_column='AgreementDefDefaultDueDay', blank=True, null=True)  # Field name made lowercase.
    agreementdefaprmethod = models.SmallIntegerField(db_column='AgreementDefAPRMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule1newbiz = models.CharField(db_column='AgreementDefRebateRule1NewBiz', max_length=8, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule1othsetl = models.CharField(db_column='AgreementDefRebateRule1OthSetl', max_length=8, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule2newbiz = models.CharField(db_column='AgreementDefRebateRule2NewBiz', max_length=18, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule2othsetl = models.CharField(db_column='AgreementDefRebateRule2OthSetl', max_length=18, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebateplanprofile = models.NullBooleanField(db_column='AgreementDefRebatePlanProfile', blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultcreditlimit = models.DecimalField(db_column='AgreementDefDefaultCreditLimit', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrevdebitinterest = models.SmallIntegerField(db_column='AgreementDefRevDebitInterest', blank=True, null=True)  # Field name made lowercase.
    agreementdefrevinterestfree = models.NullBooleanField(db_column='AgreementDefRevInterestFree', blank=True, null=True)  # Field name made lowercase.
    agreementdefsettlementadjustmentpc = models.DecimalField(db_column='AgreementDefSettlementAdjustmentPC', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefcasubmittype = models.SmallIntegerField(db_column='AgreementDefCASubmitType', blank=True, null=True)  # Field name made lowercase.
    agreementdefclawbackvalidterm = models.SmallIntegerField(db_column='AgreementDefClawbackValidTerm', blank=True, null=True)  # Field name made lowercase.
    agreementdefupliftignored = models.NullBooleanField(db_column='AgreementDefUpliftIgnored', blank=True, null=True)  # Field name made lowercase.
    agreementdefrebatevaliduntilmindays = models.SmallIntegerField(db_column='AgreementDefRebateValidUntilMinDays', blank=True, null=True)  # Field name made lowercase.
    agreementdefrecurringinspercent = models.DecimalField(db_column='AgreementDefRecurringInsPercent', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdeffeepercent = models.DecimalField(db_column='AgreementDefFeePercent', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdeffeeminimum = models.DecimalField(db_column='AgreementDefFeeMinimum', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefusebacsforpayouts = models.NullBooleanField(db_column='AgreementDefUseBACSForPayouts', blank=True, null=True)  # Field name made lowercase.
    agreementdefpvratenb = models.DecimalField(db_column='AgreementDefPVRateNB', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefpvratess = models.DecimalField(db_column='AgreementDefPVRateSS', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebatesaddintr2irrbal = models.NullBooleanField(db_column='AgreementDefRebatesAddIntr2IRRBal', blank=True, null=True)  # Field name made lowercase.
    agreementdefallowtypechange = models.CharField(db_column='AgreementDefAllowTypeChange', max_length=100, blank=True, null=True)  # Field name made lowercase.
    agreementdeffhbrvariance = models.DecimalField(db_column='AgreementDefFHBRVariance', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefpaycurrency = models.CharField(db_column='AgreementDefPayCurrency', max_length=3, blank=True, null=True)  # Field name made lowercase.
    agreementdefexcludeextraamounts = models.NullBooleanField(db_column='AgreementDefExcludeExtraAmounts', blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultforunregulated = models.SmallIntegerField(db_column='AgreementDefDefaultForUnregulated', blank=True, null=True)  # Field name made lowercase.
    agreementdefvardailyintrmethod = models.SmallIntegerField(db_column='AgreementDefVarDailyIntrMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefvarvariety1stpayment = models.NullBooleanField(db_column='AgreementDefVarVariety1stPayment', blank=True, null=True)  # Field name made lowercase.
    agreementdefreqautocollectoption = models.NullBooleanField(db_column='AgreementDefReqAutoCollectOption', blank=True, null=True)  # Field name made lowercase.
    agreementdefbasecurrencyseq = models.SmallIntegerField(db_column='AgreementDefBaseCurrencySeq')  # Field name made lowercase.
    agreementdefpaycurrencyseq = models.SmallIntegerField(db_column='AgreementDefPayCurrencySeq')  # Field name made lowercase.
    agreementdefreloansetagreedate = models.CharField(db_column='AgreementDefReloanSetAgreeDate', max_length=100, blank=True, null=True)  # Field name made lowercase.
    agreementdefcompanybankid = models.IntegerField(db_column='AgreementDefCompanyBankID')  # Field name made lowercase.
    agreementdefaddinterestonlyperiod = models.NullBooleanField(db_column='AgreementDefAddInterestOnlyPeriod', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod3 = models.TextField(db_column='AgreementDefSageMethod3', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod3 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod3', blank=True, null=True)  # Field name made lowercase.
    agreementdefnosecondaryrental = models.SmallIntegerField(db_column='AgreementDefNoSecondaryRental', blank=True, null=True)  # Field name made lowercase.
    agreementdefsecondaryrentalfrequency = models.SmallIntegerField(db_column='AgreementDefSecondaryRentalFrequency', blank=True, null=True)  # Field name made lowercase.
    agreementdefsecondaryrentaluseprimaryfrequency = models.SmallIntegerField(db_column='AgreementDefSecondaryRentalUsePrimaryFrequency', blank=True, null=True)  # Field name made lowercase.
    agreementdefsecondaryrentaldefaultterm = models.SmallIntegerField(db_column='AgreementDefSecondaryRentalDefaultTerm', blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterepaymentfee = models.DecimalField(db_column='AgreementDefRebateRepaymentFee', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule4year1 = models.DecimalField(db_column='AgreementDefRebateRule4Year1', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule4year2 = models.DecimalField(db_column='AgreementDefRebateRule4Year2', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule4year3 = models.DecimalField(db_column='AgreementDefRebateRule4Year3', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule4year4 = models.DecimalField(db_column='AgreementDefRebateRule4Year4', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule4year5 = models.DecimalField(db_column='AgreementDefRebateRule4Year5', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod4 = models.TextField(db_column='AgreementDefSageMethod4', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod4 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod4', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod5 = models.TextField(db_column='AgreementDefSageMethod5', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod5 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod5', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod6 = models.TextField(db_column='AgreementDefSageMethod6', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod6 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod6', blank=True, null=True)  # Field name made lowercase.
    agreementdefaprdaily = models.NullBooleanField(db_column='AgreementDefAPRDaily', blank=True, null=True)  # Field name made lowercase.
    agreementdefsectionofmonth = models.SmallIntegerField(db_column='AgreementDefSectionOfMonth', blank=True, null=True)  # Field name made lowercase.
    agreementdefdayofweek = models.SmallIntegerField(db_column='AgreementDefDayOfWeek', blank=True, null=True)  # Field name made lowercase.
    agreementdefdebitintrno = models.SmallIntegerField(db_column='AgreementDefDebitIntrNo', blank=True, null=True)  # Field name made lowercase.
    agreementdefpenaltyintrno = models.SmallIntegerField(db_column='AgreementDefPenaltyIntrNo', blank=True, null=True)  # Field name made lowercase.
    agreementdefvar1stpaymentdaily = models.NullBooleanField(db_column='AgreementDefVar1stPaymentDaily', blank=True, null=True)  # Field name made lowercase.
    agreementdefappduemethod = models.SmallIntegerField(db_column='AgreementDefAppDueMethod', blank=True, null=True)  # Field name made lowercase.
    agreementdefdailyratechange = models.NullBooleanField(db_column='AgreementDefDailyRateChange', blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultsubsidy1 = models.CharField(db_column='AgreementDefDefaultSubsidy1', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultsubsidy2 = models.CharField(db_column='AgreementDefDefaultSubsidy2', max_length=10, blank=True, null=True)  # Field name made lowercase.
    agreementdefregwarningtype = models.SmallIntegerField(db_column='AgreementDefRegWarningType', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod7 = models.TextField(db_column='AgreementDefSageMethod7', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod7 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod7', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod8 = models.TextField(db_column='AgreementDefSageMethod8', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod8 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod8', blank=True, null=True)  # Field name made lowercase.
    agreementdefvarintronwhat = models.SmallIntegerField(db_column='AgreementDefVarIntrOnWhat', blank=True, null=True)  # Field name made lowercase.
    agreementdefusevatratetable = models.NullBooleanField(db_column='AgreementDefUseVatRateTable', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod9 = models.TextField(db_column='AgreementDefSageMethod9', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod9 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod9', blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule4 = models.SmallIntegerField(db_column='AgreementDefRebateRule4', blank=True, null=True)  # Field name made lowercase.
    agreementdefpayoutsdefaultdone = models.NullBooleanField(db_column='AgreementDefPayoutsDefaultDone', blank=True, null=True)  # Field name made lowercase.
    agreementdefsecondaryrentalauto = models.NullBooleanField(db_column='AgreementDefSecondaryRentalAuto', blank=True, null=True)  # Field name made lowercase.
    agreementdefrevcreditinitialprincipal = models.NullBooleanField(db_column='AgreementDefRevCreditInitialPrincipal', blank=True, null=True)  # Field name made lowercase.
    agreementdefstatementrequired = models.NullBooleanField(db_column='AgreementDefStatementRequired', blank=True, null=True)  # Field name made lowercase.
    agreementdefccddefault = models.NullBooleanField(db_column='AgreementDefCCDDefault', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod10 = models.TextField(db_column='AgreementDefSageMethod10', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod10 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod10', blank=True, null=True)  # Field name made lowercase.
    agreementdefnodeferment = models.NullBooleanField(db_column='AgreementDefNoDeferment', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod11 = models.TextField(db_column='AgreementDefSageMethod11', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod11 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod11', blank=True, null=True)  # Field name made lowercase.
    agreementdefcalcchargesdeferredresidual = models.NullBooleanField(db_column='AgreementDefCalcChargesDeferredResidual', blank=True, null=True)  # Field name made lowercase.
    agreementdefcalcchargesdeferredfirstpay = models.NullBooleanField(db_column='AgreementDefCalcChargesDeferredFirstPay', blank=True, null=True)  # Field name made lowercase.
    agreementdefcalcchargesexcludenoupfronts = models.NullBooleanField(db_column='AgreementDefCalcChargesExcludeNoUpfronts', blank=True, null=True)  # Field name made lowercase.
    agreementdefcalcchargesdeferredfirstyield = models.NullBooleanField(db_column='AgreementDefCalcChargesDeferredFirstYield', blank=True, null=True)  # Field name made lowercase.
    agreementdefadvancearrears = models.SmallIntegerField(db_column='AgreementDefAdvanceArrears', blank=True, null=True)  # Field name made lowercase.
    agreementdefcreditarrears = models.SmallIntegerField(db_column='AgreementDefCreditArrears', blank=True, null=True)  # Field name made lowercase.
    agreementdefccasetflag = models.NullBooleanField(db_column='AgreementDefCCASetFlag', blank=True, null=True)  # Field name made lowercase.
    agreementdefccdsetflag = models.NullBooleanField(db_column='AgreementDefCCDSetFlag', blank=True, null=True)  # Field name made lowercase.
    agreementdefccdminprincipal = models.DecimalField(db_column='AgreementDefCCDMinPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefccdmaxprincipal = models.DecimalField(db_column='AgreementDefCCDMaxPrincipal', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefccdcustomertypes = models.IntegerField(db_column='AgreementDefCCDCustomerTypes', blank=True, null=True)  # Field name made lowercase.
    agreementdefregulatedoveridecommercial = models.DecimalField(db_column='AgreementDefRegulatedOverideCommercial', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefirrdiscountrate = models.DecimalField(db_column='AgreementDefIRRDiscountRate', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefirrdiscountprin = models.DecimalField(db_column='AgreementDefIRRDiscountPrin', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefdealerdd = models.NullBooleanField(db_column='AgreementDefDealerDD', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagecompanyid = models.IntegerField(db_column='AgreementDefSageCompanyId', blank=True, null=True)  # Field name made lowercase.
    agreementdefenableccp = models.NullBooleanField(db_column='AgreementDefEnableCCP', blank=True, null=True)  # Field name made lowercase.
    agreementdefp2pfunder = models.NullBooleanField(db_column='AgreementDefP2PFunder', blank=True, null=True)  # Field name made lowercase.
    agreementdefshowcapcom = models.NullBooleanField(db_column='AgreementDefShowCapCom', blank=True, null=True)  # Field name made lowercase.
    agreementdefignoreteletrack = models.NullBooleanField(db_column='AgreementDefIgnoreTeleTrack', blank=True, null=True)  # Field name made lowercase.
    agreementdefcalcdailyflatrate = models.NullBooleanField(db_column='AgreementDefCalcDailyFlatRate', blank=True, null=True)  # Field name made lowercase.
    agreementdefinvoicesrequired = models.NullBooleanField(db_column='AgreementDefInvoicesRequired', blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultpenintrmaxdays = models.SmallIntegerField(db_column='AgreementDefDefaultPenIntrMaxDays', blank=True, null=True)  # Field name made lowercase.
    agreementdefaddpenintrdaily = models.NullBooleanField(db_column='AgreementDefAddPenIntrDaily', blank=True, null=True)  # Field name made lowercase.
    agreementdefduextracalc = models.NullBooleanField(db_column='AgreementDefDUExtraCalc', blank=True, null=True)  # Field name made lowercase.
    agreementdefsulco = models.NullBooleanField(db_column='AgreementDefSULCO', blank=True, null=True)  # Field name made lowercase.
    agreementdefrebatemethodtext = models.CharField(db_column='AgreementDefRebateMethodText', max_length=20, blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultinternalpayout = models.DecimalField(db_column='AgreementDefDefaultInternalPayout', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultacquisproductcode = models.CharField(db_column='AgreementDefDefaultACQUISProductCode', max_length=7, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5label1 = models.CharField(db_column='AgreementDefRebateRule5Label1', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5percent1 = models.DecimalField(db_column='AgreementDefRebateRule5Percent1', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5label2 = models.CharField(db_column='AgreementDefRebateRule5Label2', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5percent2 = models.DecimalField(db_column='AgreementDefRebateRule5Percent2', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5label3 = models.CharField(db_column='AgreementDefRebateRule5Label3', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5percent3 = models.DecimalField(db_column='AgreementDefRebateRule5Percent3', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5label4 = models.CharField(db_column='AgreementDefRebateRule5Label4', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5percent4 = models.DecimalField(db_column='AgreementDefRebateRule5Percent4', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5label5 = models.CharField(db_column='AgreementDefRebateRule5Label5', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5percent5 = models.DecimalField(db_column='AgreementDefRebateRule5Percent5', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5label6 = models.CharField(db_column='AgreementDefRebateRule5Label6', max_length=30, blank=True, null=True)  # Field name made lowercase.
    agreementdefrebaterule5percent6 = models.DecimalField(db_column='AgreementDefRebateRule5Percent6', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefoutputirrbalance = models.NullBooleanField(db_column='AgreementDefOutputIRRBalance', blank=True, null=True)  # Field name made lowercase.
    agreementdefhcst = models.NullBooleanField(db_column='AgreementDefHCST', blank=True, null=True)  # Field name made lowercase.
    agreementdefdailyratemax = models.DecimalField(db_column='AgreementDefDailyRateMax', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdeftotalchargesmax = models.DecimalField(db_column='AgreementDefTotalChargesMax', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdeffeesmax = models.DecimalField(db_column='AgreementDefFeesMax', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefrowfee = models.DecimalField(db_column='AgreementDefROWFee', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefadjustfinalpayrdg = models.NullBooleanField(db_column='AgreementDefAdjustFinalPayRdg', blank=True, null=True)  # Field name made lowercase.
    agreementdefvatpayoutamount = models.NullBooleanField(db_column='AgreementDefVATPayoutAmount', blank=True, null=True)  # Field name made lowercase.
    agreementdefappmethodupfront = models.SmallIntegerField(db_column='AgreementDefAppMethodUpfront', blank=True, null=True)  # Field name made lowercase.
    agreementdefappmethodresidual = models.SmallIntegerField(db_column='AgreementDefAppMethodResidual', blank=True, null=True)  # Field name made lowercase.
    agreementdefratechangeaffectresidual = models.NullBooleanField(db_column='AgreementDefRateChangeAffectResidual', blank=True, null=True)  # Field name made lowercase.
    agreementdefdisplaychargesuplift = models.NullBooleanField(db_column='AgreementDefDisplayChargesUplift', blank=True, null=True)  # Field name made lowercase.
    agreementdefsagemethod12 = models.TextField(db_column='AgreementDefSageMethod12', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    agreementdefignoresagemethod12 = models.NullBooleanField(db_column='AgreementDefIgnoreSageMethod12', blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultrebatereg = models.SmallIntegerField(db_column='AgreementDefDefaultRebateReg', blank=True, null=True)  # Field name made lowercase.
    agreementdefdefaultrebateunreg = models.SmallIntegerField(db_column='AgreementDefDefaultRebateUnReg', blank=True, null=True)  # Field name made lowercase.
    agreementdefcompoundcommission = models.NullBooleanField(db_column='AgreementDefCompoundCommission', blank=True, null=True)  # Field name made lowercase.
    agreementdefinvoicefrequency = models.SmallIntegerField(db_column='AgreementDefInvoiceFrequency', blank=True, null=True)  # Field name made lowercase.
    agreementdefcalcintrcompoundcomm = models.NullBooleanField(db_column='AgreementDefCalcIntrCompoundComm', blank=True, null=True)  # Field name made lowercase.
    agreementdefincluderesidualforicbreport = models.NullBooleanField(db_column='AgreementDefIncludeResidualforICBReport', blank=True, null=True)  # Field name made lowercase.
    agreementdefpmtprofiledaily = models.NullBooleanField(db_column='AgreementDefPMTProfileDaily', blank=True, null=True)  # Field name made lowercase.
    agreementdefmcobuplift = models.DecimalField(db_column='AgreementDefMCOBUplift', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    agreementdefacclinkposttype = models.SmallIntegerField(db_column='AgreementDefAccLinkPostType', blank=True, null=True)  # Field name made lowercase.
    agreementdefguarantorpayout = models.NullBooleanField(db_column='AgreementDefGuarantorPayout', blank=True, null=True)  # Field name made lowercase.
    agreementdefnperflexible = models.NullBooleanField(db_column='AgreementDefNPerFlexible', blank=True, null=True)  # Field name made lowercase.
    agreementdefshowcompintr = models.NullBooleanField(db_column='AgreementDefShowCompIntr', blank=True, null=True)  # Field name made lowercase.
    agreementdefautocalculaterate = models.NullBooleanField(db_column='AgreementDefAutoCalculateRate', blank=True, null=True)  # Field name made lowercase.
    agreementdefuseseasonalprofiles = models.NullBooleanField(db_column='AgreementDefUseSeasonalProfiles', blank=True, null=True)  # Field name made lowercase.
    agreementdefseasonalprofilemaxterm = models.IntegerField(db_column='AgreementDefSeasonalProfileMaxTerm', blank=True, null=True)  # Field name made lowercase.
    agreementdefsettlementmessagename = models.CharField(db_column='AgreementDefSettlementMessageName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementdefcpendmessagename = models.CharField(db_column='AgreementDefCPEndMessageName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    agreementdefrevcreditcollectintronly = models.NullBooleanField(db_column='AgreementDefRevCreditCollectIntrOnly', blank=True, null=True)  # Field name made lowercase.
    agreementdefrevcreditaddmonths = models.SmallIntegerField(db_column='AgreementDefRevCreditAddMonths', blank=True, null=True)  # Field name made lowercase.
    agreementdefrevcreditadddays = models.SmallIntegerField(db_column='AgreementDefRevCreditAddDays', blank=True, null=True)  # Field name made lowercase.
    agreementdefresidualpaid3rdparty = models.SmallIntegerField(db_column='AgreementDefResidualPaid3rdParty', blank=True, null=True)  # Field name made lowercase.
    agreementdefwarningmessage = models.CharField(db_column='AgreementDefWarningMessage', max_length=200, blank=True, null=True)  # Field name made lowercase.
    agreementdefuseownplannedsettings = models.NullBooleanField(db_column='AgreementDefUseOwnPlannedSettings', blank=True, null=True)  # Field name made lowercase.
    agreementdefusemultirate = models.NullBooleanField(db_column='AgreementDefUseMultiRate', blank=True, null=True)  # Field name made lowercase.
    agreementdef3rdpartyresidualagreeid = models.SmallIntegerField(db_column='AgreementDef3rdPartyResidualAgreeID', blank=True, null=True)  # Field name made lowercase.
    agreementdef3rdpartyresidualgrace = models.SmallIntegerField(db_column='AgreementDef3rdPartyResidualGrace', blank=True, null=True)  # Field name made lowercase.
    agreementdefinterestratetype = models.SmallIntegerField(db_column='AgreementDefInterestRateType', blank=True, null=True)  # Field name made lowercase.
    agreementdefsetvaliduntildate = models.NullBooleanField(db_column='AgreementDefSetValidUntilDate', blank=True, null=True)  # Field name made lowercase.
    selectable = models.NullBooleanField(db_column='selectable', blank=True, null=True)

    class Meta:
        verbose_name = 'Agreement Definition'
        verbose_name_plural = 'Agreement Definitions'

    def __str__(self):
        return '{}'.format(self.agreementdefname)


class go_customers(models.Model):
    customernumber = models.CharField(db_column='CustomerNumber', max_length=10, unique=True)  # Field name made lowercase.
    customersurname = models.CharField(db_column='CustomerSurName', max_length=40, blank=True, null=True)  # Field name made lowercase.
    customerfirstname = models.CharField(db_column='CustomerFirstname', max_length=40, blank=True, null=True)  # Field name made lowercase.
    customertitle = models.CharField(db_column='CustomerTitle', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customercompany = models.CharField(db_column='CustomerCompany', max_length=60, blank=True, null=True)  # Field name made lowercase.
    customerlettertext = models.CharField(db_column='CustomerLetterText', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customeraddress1 = models.CharField(db_column='CustomerAddress1', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customeraddress2 = models.CharField(db_column='CustomerAddress2', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customeraddress3 = models.CharField(db_column='CustomerAddress3', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customeraddress4 = models.CharField(db_column='CustomerAddress4', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customeraddress5 = models.CharField(db_column='CustomerAddress5', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customerpostcode = models.CharField(db_column='CustomerPostcode', max_length=8, blank=True, null=True)  # Field name made lowercase.
    customerdateofbirth = models.DateTimeField(db_column='CustomerDateOfBirth', blank=True, null=True)  # Field name made lowercase.
    customerrescode = models.CharField(db_column='CustomerResCode', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerphonenumber = models.CharField(db_column='CustomerPhoneNumber', max_length=25, blank=True, null=True)  # Field name made lowercase.
    customeroccupation = models.CharField(db_column='CustomerOccupation', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customercreator = models.CharField(db_column='CustomerCreator', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customeramendor = models.CharField(db_column='CustomerAmendor', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customershortname = models.CharField(db_column='CustomerShortName', max_length=5, blank=True, null=True)  # Field name made lowercase.
    customercontact = models.CharField(db_column='CustomerContact', max_length=100, blank=True, null=True)  # Field name made lowercase.
    customerstatus = models.CharField(db_column='CustomerStatus', max_length=150, blank=True, null=True)  # Field name made lowercase.
    customermarital = models.CharField(db_column='CustomerMarital', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customertenure = models.CharField(db_column='CustomerTenure', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerninumber = models.CharField(db_column='CustomerNINumber', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customernotes = models.TextField(db_column='CustomerNotes', blank=True, null=True)  # Field name made lowercase.
    customercreatedate = models.DateTimeField(db_column='CustomerCreateDate', blank=True, null=True)  # Field name made lowercase.
    customeramenddate = models.DateTimeField(db_column='CustomerAmendDate', blank=True, null=True)  # Field name made lowercase.
    customercomphousenumber = models.CharField(db_column='CustomerCompHouseNumber', max_length=6, blank=True, null=True)  # Field name made lowercase.
    customercompstreetname = models.CharField(db_column='CustomerCompStreetName', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customercomptownname = models.CharField(db_column='CustomerCompTownName', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerbankaccountname = models.CharField(db_column='CustomerBankAccountName', max_length=20, blank=True, null=True)  # Field name made lowercase.
    customerbanksortcode = models.CharField(db_column='CustomerBankSortCode', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customerbankaccountnumber = models.CharField(db_column='CustomerBankAccountNumber', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customergender = models.CharField(db_column='CustomerGender', max_length=1, blank=True, null=True)  # Field name made lowercase.
    customerborrower = models.NullBooleanField(db_column='CustomerBorrower', blank=True, null=True)  # Field name made lowercase.
    customerguarantor = models.NullBooleanField(db_column='CustomerGuarantor', blank=True, null=True)  # Field name made lowercase.
    customergroup = models.IntegerField(db_column='CustomerGroup', blank=True, null=True)  # Field name made lowercase.
    customercommercial = models.NullBooleanField(db_column='CustomerCommercial', blank=True, null=True)  # Field name made lowercase.
    customerfaxnumber = models.CharField(db_column='CustomerFaxNumber', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customercontactpos = models.CharField(db_column='CustomerContactPos', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customercontact2 = models.CharField(db_column='CustomerContact2', max_length=100, blank=True, null=True)  # Field name made lowercase.
    customercontactpos2 = models.CharField(db_column='CustomerContactPos2', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customertypeofbusiness = models.CharField(db_column='CustomerTypeofBusiness', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerbusinessstate = models.CharField(db_column='CustomerBusinessState', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerbusinessstatedate = models.DateTimeField(db_column='CustomerBusinessStateDate', blank=True, null=True)  # Field name made lowercase.
    customertypeofsecurity = models.CharField(db_column='CustomerTypeofSecurity', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customersecuritypercentage = models.CharField(db_column='CustomerSecurityPercentage', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerr185required = models.CharField(db_column='CustomerR185Required', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customeraccountingyearend = models.CharField(db_column='CustomerAccountingYearEnd', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerlastaccounts = models.DateTimeField(db_column='CustomerLastAccounts', blank=True, null=True)  # Field name made lowercase.
    customerignoreletters = models.TextField(db_column='CustomerIgnoreLetters', blank=True, null=True)  # Field name made lowercase.
    customerinitial = models.CharField(db_column='Customerinitial', max_length=1, blank=True, null=True)  # Field name made lowercase.
    customertimeataddressyy = models.IntegerField(db_column='CustomerTimeAtAddressYY', blank=True, null=True)  # Field name made lowercase.
    customertimeataddressmm = models.IntegerField(db_column='CustomerTimeAtAddressMM', blank=True, null=True)  # Field name made lowercase.
    customerresidentstatus = models.CharField(db_column='CustomerResidentStatus', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customeroccupationcode = models.CharField(db_column='CustomerOccupationCode', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customeroccupationdescription = models.CharField(db_column='CustomerOccupationDescription', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerregistrationnumber = models.CharField(db_column='CustomerRegistrationNumber', max_length=20, blank=True, null=True)  # Field name made lowercase.
    customervatnumber = models.CharField(db_column='CustomerVatNumber', max_length=20, blank=True, null=True)  # Field name made lowercase.
    customerdateestablished = models.CharField(db_column='CustomerDateEstablished', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customercreditorname = models.CharField(db_column='CustomerCreditorName', max_length=20, blank=True, null=True)  # Field name made lowercase.
    customercreditoraccountnumber = models.CharField(db_column='CustomerCreditorAccountNumber', max_length=20, blank=True, null=True)  # Field name made lowercase.
    customercreditorbalanceoutstanding = models.DecimalField(db_column='CustomerCreditorBalanceOutstanding', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customercreditormonthlyrepayment = models.DecimalField(db_column='CustomerCreditorMonthlyRepayment', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customerpropertyinname = models.CharField(db_column='CustomerPropertyInName', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerpropertyvalue = models.DecimalField(db_column='CustomerPropertyValue', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customermortgage = models.DecimalField(db_column='CustomerMortgage', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customersecondmortgage = models.DecimalField(db_column='CustomerSecondMortgage', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customerpropertyequity = models.DecimalField(db_column='CustomerPropertyEquity', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customerleaseperodremaining = models.IntegerField(db_column='CustomerLeasePerodRemaining', blank=True, null=True)  # Field name made lowercase.
    customerlandlord = models.CharField(db_column='CustomerLandlord', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerpreviousaddress1 = models.CharField(db_column='CustomerPreviousAddress1', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customerpreviousaddress2 = models.CharField(db_column='CustomerPreviousAddress2', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customerpreviousaddress3 = models.CharField(db_column='CustomerPreviousAddress3', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customerpreviousaddress4 = models.CharField(db_column='CustomerPreviousAddress4', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customerpreviousaddress5 = models.CharField(db_column='CustomerPreviousAddress5', max_length=35, blank=True, null=True)  # Field name made lowercase.
    customerprevioustimeataddressyy = models.IntegerField(db_column='CustomerPreviousTimeAtAddressYY', blank=True, null=True)  # Field name made lowercase.
    customerprevioustimeataddressmm = models.IntegerField(db_column='CustomerPreviousTimeAtAddressMM', blank=True, null=True)  # Field name made lowercase.
    customerpreviouspostcode = models.CharField(db_column='CustomerPreviousPostcode', max_length=8, blank=True, null=True)  # Field name made lowercase.
    customerprevioustenure = models.CharField(db_column='CustomerPreviousTenure', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customeremployeraddress = models.CharField(db_column='CustomerEmployerAddress', max_length=200, blank=True, null=True)  # Field name made lowercase.
    customergrosssalary = models.DecimalField(db_column='CustomerGrossSalary', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customernetsalary = models.DecimalField(db_column='CustomerNetSalary', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customeremploymentstartdate = models.DateTimeField(db_column='CustomerEmploymentStartDate', blank=True, null=True)  # Field name made lowercase.
    customeremploymentenddate = models.DateTimeField(db_column='CustomerEmploymentEndDate', blank=True, null=True)  # Field name made lowercase.
    customertimeinemploymentyy = models.IntegerField(db_column='CustomerTimeInEmploymentYY', blank=True, null=True)  # Field name made lowercase.
    customertimeinemploymentmm = models.IntegerField(db_column='CustomerTimeInEmploymentMM', blank=True, null=True)  # Field name made lowercase.
    customerpreviousoccupationcode = models.CharField(db_column='CustomerPreviousOccupationCode', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerpreviousoccupation = models.CharField(db_column='CustomerPreviousOccupation', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerpreviousemployername = models.CharField(db_column='CustomerPreviousEmployerName', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerpreviousemployeraddress = models.CharField(db_column='CustomerPreviousEmployerAddress', max_length=200, blank=True, null=True)  # Field name made lowercase.
    customerpreviousemployertelno = models.CharField(db_column='CustomerPreviousEmployerTelNo', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerpreviousemploymentstartdate = models.DateTimeField(db_column='CustomerPreviousEmploymentStartDate', blank=True, null=True)  # Field name made lowercase.
    customerpreviousemploymentenddate = models.DateTimeField(db_column='CustomerPreviousEmploymentEndDate', blank=True, null=True)  # Field name made lowercase.
    customerprevioustimeinemploymentyy = models.IntegerField(db_column='CustomerPreviousTimeInEmploymentYY', blank=True, null=True)  # Field name made lowercase.
    customerprevioustimeinemploymentmm = models.IntegerField(db_column='CustomerPreviousTimeInEmploymentMM', blank=True, null=True)  # Field name made lowercase.
    customerpreviousgrosssalary = models.DecimalField(db_column='CustomerPreviousGrossSalary', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customervisa = models.NullBooleanField(db_column='CustomerVisa', blank=True, null=True)  # Field name made lowercase.
    customeraccess = models.NullBooleanField(db_column='CustomerAccess', blank=True, null=True)  # Field name made lowercase.
    customerdebitcard = models.NullBooleanField(db_column='CustomerDebitCard', blank=True, null=True)  # Field name made lowercase.
    customerstorecard = models.NullBooleanField(db_column='CustomerStoreCard', blank=True, null=True)  # Field name made lowercase.
    customeramericanexpress = models.NullBooleanField(db_column='CustomerAmericanExpress', blank=True, null=True)  # Field name made lowercase.
    customerchequeguarantee = models.NullBooleanField(db_column='CustomerChequeGuarantee', blank=True, null=True)  # Field name made lowercase.
    customertenureprevious = models.CharField(db_column='CustomerTenurePrevious', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerdependantchildren = models.IntegerField(db_column='CustomerDependantChildren', blank=True, null=True)  # Field name made lowercase.
    customertype = models.IntegerField(db_column='CustomerType', blank=True, null=True)  # Field name made lowercase.
    customeremployerpostcode = models.CharField(db_column='CustomerEmployerPostCode', max_length=8, blank=True, null=True)  # Field name made lowercase.
    customerpreviousemployerpostcode = models.CharField(db_column='CustomerPreviousEmployerPostCode', max_length=10, blank=True, null=True)  # Field name made lowercase.
    customername = models.CharField(db_column='CustomerName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customeryearstrading = models.IntegerField(db_column='CustomerYearsTrading', blank=True, null=True)  # Field name made lowercase.
    customertimeataddress = models.IntegerField(db_column='CustomerTimeAtAddress', blank=True, null=True)  # Field name made lowercase.
    customeryearsemployed = models.IntegerField(db_column='CustomerYearsEmployed', blank=True, null=True)  # Field name made lowercase.
    customermonthsemployed = models.IntegerField(db_column='CustomerMonthsEmployed', blank=True, null=True)  # Field name made lowercase.
    customeremployertelno = models.CharField(db_column='CustomerEmployerTelNo', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerdriverno = models.CharField(db_column='CustomerDriverNo', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerage = models.CharField(db_column='CustomerAge', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnesstitle = models.CharField(db_column='CustomerWitnessTitle', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnessname = models.CharField(db_column='CustomerWitnessName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnessfirstname = models.CharField(db_column='CustomerWitnessFirstName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnesssurname = models.CharField(db_column='CustomerWitnessSurname', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnessaddress1 = models.CharField(db_column='CustomerWitnessAddress1', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnessaddress2 = models.CharField(db_column='CustomerWitnessAddress2', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnessaddress3 = models.CharField(db_column='CustomerWitnessAddress3', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnessaddress4 = models.CharField(db_column='CustomerWitnessAddress4', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnessaddress5 = models.CharField(db_column='CustomerWitnessAddress5', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnesspostcode = models.CharField(db_column='CustomerWitnessPostCode', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnesstelno = models.CharField(db_column='CustomerWitnessTelNo', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerwitnessoccupation = models.CharField(db_column='CustomerWitnessOccupation', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customermobilenumber = models.CharField(db_column='CustomerMobileNumber', max_length=25, blank=True, null=True)  # Field name made lowercase.
    customercompanynumber = models.CharField(db_column='CustomerCompanyNumber', max_length=25, blank=True, null=True)  # Field name made lowercase.
    customermiddlename = models.CharField(db_column='CustomerMiddleName', max_length=40, blank=True, null=True)  # Field name made lowercase.
    customerenvelopetext = models.CharField(db_column='CustomerEnvelopeText', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerapproval = models.NullBooleanField(db_column='CustomerApproval', blank=True, null=True)  # Field name made lowercase.
    customerapprovalamount = models.DecimalField(db_column='CustomerApprovalAmount', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customerapprovaldate = models.DateTimeField(db_column='CustomerApprovalDate', blank=True, null=True)  # Field name made lowercase.
    customerapprovalexpiry = models.DateTimeField(db_column='CustomerApprovalExpiry', blank=True, null=True)  # Field name made lowercase.
    customerapprovalby = models.CharField(db_column='CustomerApprovalBy', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerexposurelimit = models.DecimalField(db_column='CustomerExposureLimit', max_digits=19, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    customersalaryverified = models.NullBooleanField(db_column='CustomerSalaryVerified', blank=True, null=True)  # Field name made lowercase.
    customersiccode = models.CharField(db_column='CustomerSICCode', max_length=20, blank=True, null=True)  # Field name made lowercase.
    customersiccodedesc = models.CharField(db_column='CustomerSICCodeDesc', max_length=100, blank=True, null=True)  # Field name made lowercase.
    customerexternalid = models.CharField(db_column='CustomerExternalID', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customeremail = models.CharField(db_column='CustomerEmail', max_length=100, blank=True, null=True)  # Field name made lowercase.
    customernationality = models.CharField(db_column='CustomerNationality', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerclosedate = models.DateTimeField(db_column='CustomerCloseDate', blank=True, null=True)  # Field name made lowercase.
    customerimagepath = models.CharField(db_column='CustomerImagePath', max_length=255, blank=True, null=True)  # Field name made lowercase.
    customercountrycode = models.CharField(db_column='CustomerCountryCode', max_length=2, blank=True, null=True)  # Field name made lowercase.
    customerbrokernumber = models.CharField(db_column='CustomerBrokerNumber', max_length=10, blank=True, null=True)  # Field name made lowercase.
    customersmsconsent = models.NullBooleanField(db_column='CustomerSMSConsent', blank=True, null=True)  # Field name made lowercase.
    customeralternativenumber = models.CharField(db_column='CustomerAlternativeNumber', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customeralternativedescription = models.CharField(db_column='CustomerAlternativeDescription', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customercorporate = models.NullBooleanField(db_column='CustomerCorporate', blank=True, null=True)  # Field name made lowercase.
    customercardavsaddress1 = models.CharField(db_column='CustomerCardAVSAddress1', max_length=200, blank=True, null=True)  # Field name made lowercase.
    customercardavsaddress2 = models.CharField(db_column='CustomerCardAVSAddress2', max_length=200, blank=True, null=True)  # Field name made lowercase.
    customercardavsaddress3 = models.CharField(db_column='CustomerCardAVSAddress3', max_length=200, blank=True, null=True)  # Field name made lowercase.
    customercardavsaddress4 = models.CharField(db_column='CustomerCardAVSAddress4', max_length=200, blank=True, null=True)  # Field name made lowercase.
    customercardavspostcode = models.CharField(db_column='CustomerCardAVSPostCode', max_length=9, blank=True, null=True)  # Field name made lowercase.
    customercardauthorizetype = models.SmallIntegerField(db_column='CustomerCardAuthorizeType', blank=True, null=True)  # Field name made lowercase.
    customercardauthcode = models.CharField(db_column='CustomerCardAuthCode', max_length=20, blank=True, null=True)  # Field name made lowercase.
    customernationalitycode = models.CharField(db_column='CustomerNationalityCode', max_length=2, blank=True, null=True)  # Field name made lowercase.
    nextsalarydate = models.DateTimeField(db_column='NextSalaryDate', blank=True, null=True)  # Field name made lowercase.
    nextsalarydateafter = models.DateTimeField(db_column='NextSalaryDateAfter', blank=True, null=True)  # Field name made lowercase.
    empperiod = models.SmallIntegerField(db_column='EmpPeriod', blank=True, null=True)  # Field name made lowercase.
    empperiodfrequency = models.SmallIntegerField(db_column='EmpPeriodFrequency', blank=True, null=True)  # Field name made lowercase.
    customeremployername = models.CharField(db_column='CustomerEmployerName', max_length=112, blank=True, null=True)  # Field name made lowercase.
    customerempcurrentposition = models.CharField(db_column='CustomerEmpCurrentPosition', max_length=100, blank=True, null=True)  # Field name made lowercase.
    customeremploymentdepartment = models.CharField(db_column='CustomerEmploymentDepartment', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerbankiban = models.CharField(db_column='CustomerBankIBAN', max_length=40, blank=True, null=True)  # Field name made lowercase.
    fcaemploystatus = models.CharField(db_column='FCAEmployStatus', max_length=30, blank=True, null=True)  # Field name made lowercase.
    customerbankbic = models.CharField(db_column='CustomerBankBIC', max_length=11, blank=True, null=True)  # Field name made lowercase.
    customercardavscv2reference = models.CharField(db_column='CustomerCardAVSCV2Reference', max_length=32, blank=True, null=True)  # Field name made lowercase.
    customersanctionnextcheckdate = models.DateTimeField(db_column='CustomerSanctionNextCheckDate', blank=True, null=True)  # Field name made lowercase.
    customeremailconsent = models.NullBooleanField(db_column='CustomerEmailConsent', blank=True, null=True)  # Field name made lowercase.
    customerpostconsent = models.NullBooleanField(db_column='CustomerPostConsent', blank=True, null=True)  # Field name made lowercase.
    customertelephoneconsent = models.NullBooleanField(db_column='CustomerTelephoneConsent', blank=True, null=True)  # Field name made lowercase.
    craupdatedcompanyname = models.NullBooleanField(db_column='CRAUpdatedCompanyName', blank=True, null=True)  # Field name made lowercase.
    customerataddressfrom = models.DateTimeField(db_column='CustomerAtAddressFrom', blank=True, null=True)  # Field name made lowercase.
    customerataddressto = models.DateTimeField(db_column='CustomerAtAddressTo', blank=True, null=True)  # Field name made lowercase.
    customerpreviousphonenumber = models.CharField(db_column='CustomerPreviousPhoneNumber', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customerpreviousresidentstatus = models.CharField(db_column='CustomerPreviousResidentStatus', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customerpreviousataddressfrom = models.DateTimeField(db_column='CustomerPreviousAtAddressFrom', blank=True, null=True)  # Field name made lowercase.
    customerpreviousataddressto = models.DateTimeField(db_column='CustomerPreviousAtAddressTo', blank=True, null=True)  # Field name made lowercase.
    customerethnicity = models.IntegerField(db_column='CustomerEthnicity', blank=True, null=True)  # Field name made lowercase.
    corporatecard = models.NullBooleanField(db_column='CorporateCard', blank=True, null=True)  # Field name made lowercase.
    mcc6012date = models.DateTimeField(db_column='MCC6012Date', blank=True, null=True)  # Field name made lowercase.
    customerpartnerdirectornumber = models.IntegerField(db_column='CustomerPartnerDirectorNumber', blank=True, null=True)  # Field name made lowercase.
    customeralternativemobilenumber = models.CharField(db_column='CustomerAlternativeMobileNumber', max_length=15, blank=True, null=True)  # Field name made lowercase.
    customercreditdebitcardno = models.CharField(db_column='CustomerCreditDebitCardNo', max_length=376, blank=True, null=True)  # Field name made lowercase.
    customercreditdebitcardissue = models.CharField(db_column='CustomerCreditDebitCardIssue', max_length=376, blank=True, null=True)  # Field name made lowercase.
    customercreditdebitcardexpiry = models.CharField(db_column='CustomerCreditDebitCardExpiry', max_length=376, blank=True, null=True)  # Field name made lowercase.
    customercreditdebitcardstart = models.CharField(db_column='CustomerCreditDebitCardStart', max_length=376, blank=True, null=True)  # Field name made lowercase.
    customercreditdebitcardholdername = models.CharField(db_column='CustomerCreditDebitCardHolderName', max_length=376, blank=True, null=True)  # Field name made lowercase.
    customersmsmarketingconsent = models.NullBooleanField(db_column='CustomerSMSMarketingConsent', blank=True, null=True)  # Field name made lowercase.
    customeremailmarketingconsent = models.NullBooleanField(db_column='CustomerEMailMarketingConsent', blank=True, null=True)  # Field name made lowercase.
    customertelephonemarketingconsent = models.NullBooleanField(db_column='CustomerTelephoneMarketingConsent', blank=True, null=True)  # Field name made lowercase.
    customerpostmarketingconsent = models.NullBooleanField(db_column='CustomerPostMarketingConsent', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        return '{}'.format(self.customernumber)


class go_agreement_querydetail(models.Model):

    go_id = models.OneToOneField('go_agreement_index', max_length=50, unique=True, null=True, on_delete=models.DO_NOTHING)

    agreementnumber = models.CharField(db_column='AgreementNumber', max_length=10, null=True, default='',
                                       unique=True)  # Field name made lowercase.
    agreementcustomernumber = models.ForeignKey('go_customers', db_column='AgreementCustomerNumber',
                                                max_length=10, blank=True, null=True, to_field="customernumber",
                                                on_delete=models.CASCADE)  # Field name made lowercase.
    customercompany = models.CharField(db_column='CustomerCompany', max_length=60, blank=True,
                                       null=True)  # Field name made lowercase.
    agreementcreator = models.CharField(db_column='AgreementCreator', max_length=15, blank=True,
                                        null=True)  # Field name made lowercase.
    agreementamendor = models.CharField(db_column='AgreementAmendor', max_length=15, blank=True,
                                        null=True)  # Field name made lowercase.
    agreementborrowers = models.CharField(db_column='AgreementBorrowers', max_length=110, blank=True,
                                          null=True)  # Field name made lowercase.
    agreementguarantors = models.CharField(db_column='AgreementGuarantors', max_length=110, blank=True,
                                           null=True)  # Field name made lowercase.
    agreementdefaultcode = models.CharField(db_column='AgreementDefaultCode', max_length=2, blank=True,
                                            null=True)  # Field name made lowercase.
    agreementinfolinkoveride = models.CharField(db_column='AgreementInfoLinkOveride', max_length=1, blank=True,
                                                null=True)  # Field name made lowercase.
    agreementstatusoveride = models.CharField(db_column='AgreementStatusOveride', max_length=1, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementspecialinstruction = models.CharField(db_column='AgreementSpecialInstruction', max_length=1,
                                                   blank=True, null=True)  # Field name made lowercase.
    agreementnameaddresschange = models.CharField(db_column='AgreementNameAddressChange', max_length=1, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementcaisflagsetting = models.CharField(db_column='AgreementCAISFlagSetting', max_length=1, blank=True,
                                                null=True)  # Field name made lowercase.
    agreementinvoicenumber = models.CharField(db_column='AgreementInvoiceNumber', max_length=10, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementnextnumber = models.CharField(db_column='AgreementNextNumber', max_length=10, blank=True,
                                           null=True)  # Field name made lowercase.
    agreementanalysiscode = models.CharField(db_column='AgreementAnalysisCode', max_length=30, blank=True,
                                             null=True)  # Field name made lowercase.
    agreementbranch = models.CharField(db_column='AgreementBranch', max_length=30, blank=True,
                                       null=True)  # Field name made lowercase.
    agreementassessofficer = models.CharField(db_column='AgreementAssessOfficer', max_length=30, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementretailoutlet = models.CharField(db_column='AgreementRetailOutlet', max_length=30, blank=True,
                                             null=True)  # Field name made lowercase.
    agreementauthority = models.CharField(db_column='AgreementAuthority', max_length=30, blank=True,
                                          null=True)  # Field name made lowercase.
    agreementmiscellaneous = models.CharField(db_column='AgreementMiscellaneous', max_length=30, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementsalessource = models.CharField(db_column='AgreementSalesSource', max_length=30, blank=True,
                                            null=True)  # Field name made lowercase.
    agreementsalesmannumber = models.CharField(db_column='AgreementSalesmanNumber', max_length=10, blank=True,
                                               null=True)  # Field name made lowercase.
    agreementdealernumber = models.CharField(db_column='AgreementDealerNumber', max_length=10, blank=True,
                                             null=True)  # Field name made lowercase.
    agreementpersonnumber = models.CharField(db_column='AgreementPersonNumber', max_length=10, blank=True,
                                             null=True)  # Field name made lowercase.
    agreementbankaccountname = models.CharField(db_column='AgreementBankAccountName', max_length=20, blank=True,
                                                null=True)  # Field name made lowercase.
    agreementbanksortcode = models.CharField(db_column='AgreementBankSortCode', max_length=15, blank=True,
                                             null=True)  # Field name made lowercase.
    agreementbankaccountnumber = models.CharField(db_column='AgreementBankAccountNumber', max_length=15, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementbankreference = models.CharField(db_column='AgreementBankReference', max_length=20, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementbankaccounttype = models.CharField(db_column='AgreementBankAccountType', max_length=1, blank=True,
                                                null=True)  # Field name made lowercase.
    agreementbanktranscode = models.CharField(db_column='AgreementBankTransCode', max_length=2, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementstatus = models.CharField(db_column='AgreementStatus', max_length=30, blank=True,
                                       null=True)  # Field name made lowercase.
    agreementintroducer = models.CharField(db_column='AgreementIntroducer', max_length=10, blank=True,
                                           null=True)  # Field name made lowercase.
    agreementautostatus = models.CharField(db_column='AgreementAutoStatus', max_length=20, blank=True,
                                           null=True)  # Field name made lowercase.
    agreementarrearsstatus = models.CharField(db_column='AgreementArrearsStatus', max_length=30, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementnumberold = models.CharField(db_column='AgreementNumberOld', max_length=10, blank=True,
                                          null=True)  # Field name made lowercase.
    agreementsiccode = models.CharField(db_column='AgreementSICCode', max_length=20, blank=True,
                                        null=True)  # Field name made lowercase.
    agreementsiccodedesc = models.CharField(db_column='AgreementSICCodeDesc', max_length=100, blank=True,
                                            null=True)  # Field name made lowercase.
    agreementintrrateid = models.CharField(db_column='AgreementIntrRateID', max_length=8, blank=True,
                                           null=True)  # Field name made lowercase.
    agreementexternalreferenceno = models.CharField(db_column='AgreementExternalReferenceNo', max_length=50,
                                                    blank=True, null=True)  # Field name made lowercase.
    agreementexternalreferenceno2 = models.CharField(db_column='AgreementExternalReferenceNo2', max_length=50,
                                                     blank=True, null=True)  # Field name made lowercase.
    agreementexternalreferenceno3 = models.CharField(db_column='AgreementExternalReferenceNo3', max_length=50,
                                                     blank=True, null=True)  # Field name made lowercase.
    agreementdepotnumber = models.CharField(db_column='AgreementDepotNumber', max_length=10, blank=True,
                                            null=True)  # Field name made lowercase.
    agreementpurpose = models.CharField(db_column='AgreementPurpose', max_length=50, blank=True,
                                        null=True)  # Field name made lowercase.
    agreementbaddebtstatus = models.CharField(db_column='AgreementBadDebtStatus', max_length=2, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementdatacashmerchantref = models.CharField(db_column='AgreementDataCashMerchantRef', max_length=30,
                                                    blank=True, null=True)  # Field name made lowercase.
    agreementprincipal = models.DecimalField(db_column='AgreementPrincipal', max_digits=19, decimal_places=4,
                                             blank=True, null=True)  # Field name made lowercase.
    agreementoriginalprincipal = models.DecimalField(db_column='AgreementOriginalPrincipal', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementcharges = models.DecimalField(db_column='AgreementCharges', max_digits=19, decimal_places=4,
                                           blank=True, null=True)  # Field name made lowercase.
    agreementtotalcostsprincipal = models.DecimalField(db_column='AgreementTotalCostsPrincipal', max_digits=19,
                                                       decimal_places=4, blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementtotalcostsinterest = models.DecimalField(db_column='AgreementTotalCostsInterest', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementdepositcash = models.DecimalField(db_column='AgreementDepositCash', max_digits=19, decimal_places=4,
                                               blank=True, null=True)  # Field name made lowercase.
    agreementdepositpartex = models.DecimalField(db_column='AgreementDepositPartEx', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementdealercommission = models.DecimalField(db_column='AgreementDealerCommission', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementdealercommissionvat = models.DecimalField(db_column='AgreementDealerCommissionVat', max_digits=19,
                                                       decimal_places=4, blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementdealercommissioninsr = models.DecimalField(db_column='AgreementDealerCommissionInsr', max_digits=19,
                                                        decimal_places=4, blank=True,
                                                        null=True)  # Field name made lowercase.
    agreementapr = models.DecimalField(db_column='AgreementAPR', max_digits=19, decimal_places=4, blank=True,
                                       null=True)  # Field name made lowercase.
    agreementextrainterest = models.DecimalField(db_column='AgreementExtraInterest', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementtotalrebates = models.DecimalField(db_column='AgreementTotalRebates', max_digits=19, decimal_places=4,
                                                blank=True, null=True)  # Field name made lowercase.
    agreementtotalwoffprincipal = models.DecimalField(db_column='AgreementTotalWOffPrincipal', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementtotalwoffinterest = models.DecimalField(db_column='AgreementTotalWOffInterest', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementextraprincipal = models.DecimalField(db_column='AgreementExtraPrincipal', max_digits=19,
                                                  decimal_places=4, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementoriginalinterest = models.DecimalField(db_column='AgreementOriginalInterest', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementtotalprincipalpaid = models.DecimalField(db_column='AgreementTotalPrincipalPaid', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementtotalinterestpaid = models.DecimalField(db_column='AgreementTotalInterestPaid', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementtotalprincipalpaidtm = models.DecimalField(db_column='AgreementTotalPrincipalPaidTM', max_digits=19,
                                                        decimal_places=4, blank=True,
                                                        null=True)  # Field name made lowercase.
    agreementtotalinterestpaidtm = models.DecimalField(db_column='AgreementTotalInterestPaidTM', max_digits=19,
                                                       decimal_places=4, blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementarrearsnetprincipal = models.DecimalField(db_column='AgreementArrearsNETPrincipal', max_digits=19,
                                                       decimal_places=4, blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementarrearsnetinterest = models.DecimalField(db_column='AgreementArrearsNETInterest', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementtotalarrearsnet = models.DecimalField(db_column='AgreementTotalArrearsNET', max_digits=19,
                                                   decimal_places=4, blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementtotalarrearsnetfee = models.DecimalField(db_column='AgreementTotalArrearsNETFee', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementtotalarrearsvatfee = models.DecimalField(db_column='AgreementTotalArrearsVatFee', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementresidualnet = models.DecimalField(db_column='AgreementResidualNET', max_digits=19, decimal_places=4,
                                               blank=True, null=True)  # Field name made lowercase.
    agreementinstalmentnet = models.DecimalField(db_column='AgreementInstalmentNET', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementcurrentbalancenet = models.DecimalField(db_column='AgreementCurrentBalanceNET', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementadvanceinstalmentnet = models.DecimalField(db_column='AgreementAdvanceInstalmentNET', max_digits=19,
                                                        decimal_places=4, blank=True,
                                                        null=True)  # Field name made lowercase.
    agreementinputvat = models.DecimalField(db_column='AgreementInputVat', max_digits=19, decimal_places=4,
                                            blank=True, null=True)  # Field name made lowercase.
    agreementoutputvat = models.DecimalField(db_column='AgreementOutputVat', max_digits=19, decimal_places=4,
                                             blank=True, null=True)  # Field name made lowercase.
    agreementresidualvat = models.DecimalField(db_column='AgreementResidualVat', max_digits=19, decimal_places=4,
                                               blank=True, null=True)  # Field name made lowercase.
    agreementadvanceinstalmentvat = models.DecimalField(db_column='AgreementAdvanceInstalmentVat', max_digits=19,
                                                        decimal_places=4, blank=True,
                                                        null=True)  # Field name made lowercase.
    agreementarrearsvat = models.DecimalField(db_column='AgreementArrearsVat', max_digits=19, decimal_places=4,
                                              blank=True, null=True)  # Field name made lowercase.
    agreementtotalpaidvat = models.DecimalField(db_column='AgreementTotalPaidVat', max_digits=19, decimal_places=4,
                                                blank=True, null=True)  # Field name made lowercase.
    agreementinstalmentvat = models.DecimalField(db_column='AgreementInstalmentVat', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementtaxdeductable = models.DecimalField(db_column='AgreementTAXDeductable', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementtaxpercentage = models.DecimalField(db_column='AgreementTAXPercentage', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementarrearstax = models.DecimalField(db_column='AgreementArrearsTAX', max_digits=19, decimal_places=4,
                                              blank=True, null=True)  # Field name made lowercase.
    agreementdebitinterest = models.DecimalField(db_column='AgreementDebitInterest', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementextraintrpaid = models.DecimalField(db_column='AgreementExtraIntrPaid', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementtotalcostspaid = models.DecimalField(db_column='AgreementTotalCostsPaid', max_digits=19,
                                                  decimal_places=4, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementtotalcharges = models.DecimalField(db_column='AgreementTotalCharges', max_digits=19, decimal_places=4,
                                                blank=True, null=True)  # Field name made lowercase.
    agreementtotalins = models.DecimalField(db_column='AgreementTotalIns', max_digits=19, decimal_places=4,
                                            blank=True, null=True)  # Field name made lowercase.
    agreementtotalfees = models.DecimalField(db_column='AgreementTotalFees', max_digits=19, decimal_places=4,
                                             blank=True, null=True)  # Field name made lowercase.
    agreementarrearstotalins = models.DecimalField(db_column='AgreementArrearsTotalINS', max_digits=19,
                                                   decimal_places=4, blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementinstalmentins = models.DecimalField(db_column='AgreementInstalmentINS', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementcurrentbalanceins = models.DecimalField(db_column='AgreementCurrentBalanceINS', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementdebitintruplift = models.DecimalField(db_column='AgreementDebitIntrUpLift', max_digits=19,
                                                   decimal_places=4, blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementdefaultbalance = models.DecimalField(db_column='AgreementDefaultBalance', max_digits=19,
                                                  decimal_places=4, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementexparrangement = models.DecimalField(db_column='AgreementExpArrangement', max_digits=19,
                                                  decimal_places=4, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementcapitalallowance = models.DecimalField(db_column='AgreementCapitalAllowance', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementtotalprincipal = models.DecimalField(db_column='AgreementTotalPrincipal', max_digits=19,
                                                  decimal_places=4, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementadditionalirrfee = models.DecimalField(db_column='AgreementAdditionalIRRFee', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementcreditlimit = models.DecimalField(db_column='AgreementCreditLimit', max_digits=19, decimal_places=4,
                                               blank=True, null=True)  # Field name made lowercase.
    agreementinsuranceapr = models.DecimalField(db_column='AgreementInsuranceAPR', max_digits=19, decimal_places=4,
                                                blank=True, null=True)  # Field name made lowercase.
    agreementintronlymnths = models.DecimalField(db_column='AgreementIntrOnlyMnths', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementgoodsdiscountrate = models.DecimalField(db_column='AgreementGoodsDiscountRate', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementbaseprincipal = models.DecimalField(db_column='AgreementBasePrincipal', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementinvoicediscountrate = models.DecimalField(db_column='AgreementInvoiceDiscountRate', max_digits=19,
                                                       decimal_places=4, blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementearlyddpayment = models.DecimalField(db_column='AgreementEarlyDDPayment', max_digits=19,
                                                  decimal_places=4, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementfhbr = models.DecimalField(db_column='AgreementFHBR', max_digits=19, decimal_places=4, blank=True,
                                        null=True)  # Field name made lowercase.
    agreementbrokerfee = models.DecimalField(db_column='AgreementBrokerFee', max_digits=19, decimal_places=4,
                                             blank=True, null=True)  # Field name made lowercase.
    agreementintrratevalue = models.DecimalField(db_column='AgreementIntrRateValue', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementsubsidy = models.DecimalField(db_column='AgreementSubsidy', max_digits=19, decimal_places=4,
                                           blank=True, null=True)  # Field name made lowercase.
    agreementnetyield = models.DecimalField(db_column='AgreementNetYield', max_digits=19, decimal_places=4,
                                            blank=True, null=True)  # Field name made lowercase.
    agreementgrossyield = models.DecimalField(db_column='AgreementGrossYield', max_digits=19, decimal_places=4,
                                              blank=True, null=True)  # Field name made lowercase.
    agreementaccruedinterest = models.DecimalField(db_column='AgreementAccruedInterest', max_digits=19,
                                                   decimal_places=4, blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementsubsidy2 = models.DecimalField(db_column='AgreementSubsidy2', max_digits=19, decimal_places=4,
                                            blank=True, null=True)  # Field name made lowercase.
    agreementbrokercommission = models.DecimalField(db_column='AgreementBrokerCommission', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementbrokercommissionvat = models.DecimalField(db_column='AgreementBrokerCommissionVat', max_digits=19,
                                                       decimal_places=4, blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementsalesmancommission = models.DecimalField(db_column='AgreementSalesmanCommission', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementaprfee = models.DecimalField(db_column='AgreementAPRFee', max_digits=19, decimal_places=4, blank=True,
                                          null=True)  # Field name made lowercase.
    agreementbaddebtprovision = models.DecimalField(db_column='AgreementBadDebtProvision', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementaprnet = models.DecimalField(db_column='AgreementAPRNet', max_digits=19, decimal_places=4, blank=True,
                                          null=True)  # Field name made lowercase.
    agreementbaddebtpercentage = models.DecimalField(db_column='AgreementBadDebtPercentage', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementrefixaddamount = models.DecimalField(db_column='AgreementRefixAddAmount', max_digits=19,
                                                  decimal_places=4, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementagreementdate = models.DateTimeField(db_column='AgreementAgreementDate', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementfirstpaymentdate = models.DateTimeField(db_column='AgreementFirstPaymentDate', blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementupfrontdate = models.DateTimeField(db_column='AgreementUpfrontDate', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementresidualdate = models.DateTimeField(db_column='AgreementResidualDate', blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementstatementdate = models.DateTimeField(db_column='AgreementStatementDate', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementcreatedate = models.DateTimeField(db_column='AgreementCreateDate', blank=True,
                                               null=True)  # Field name made lowercase.
    agreementamenddate = models.DateTimeField(db_column='AgreementAmendDate', blank=True,
                                              null=True)  # Field name made lowercase.
    agreementsettleddate = models.DateTimeField(db_column='AgreementSettledDate', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementlastduedate = models.DateTimeField(db_column='AgreementLastDueDate', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementnextduedate = models.DateTimeField(db_column='AgreementNextDueDate', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementintrstartdate = models.DateTimeField(db_column='AgreementIntrStartDate', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementdefaultdate = models.DateTimeField(db_column='AgreementDefaultDate', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementnumberchangeexperiandate = models.DateTimeField(db_column='AgreementNumberChangeExperianDate',
                                                             blank=True, null=True)  # Field name made lowercase.
    agreementnumberchangeequifaxdate = models.DateTimeField(db_column='AgreementNumberChangeEquifaxDate',
                                                            blank=True, null=True)  # Field name made lowercase.
    agreementearlydddate = models.DateTimeField(db_column='AgreementEarlyDDDate', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementintrratedateset = models.DateTimeField(db_column='AgreementIntrRateDateSet', blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementintrraterefixdate = models.DateTimeField(db_column='AgreementIntrRateRefixDate', blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementexperiancloseddate = models.DateTimeField(db_column='AgreementExperianClosedDate', blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementintronlystartdate = models.DateTimeField(db_column='AgreementIntrOnlyStartDate', blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementnextstatementdate = models.DateTimeField(db_column='AgreementNextStatementDate', blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementdiscountdate1 = models.DateTimeField(db_column='AgreementDiscountDate1', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementdiscountdate2 = models.DateTimeField(db_column='AgreementDiscountDate2', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementfrozendate = models.DateTimeField(db_column='AgreementFrozenDate', blank=True,
                                               null=True)  # Field name made lowercase.
    agreementbaddebtdate = models.DateTimeField(db_column='AgreementBadDebtDate', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementpaymentmethod = models.SmallIntegerField(db_column='AgreementPaymentMethod', blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementnumpayments = models.SmallIntegerField(db_column='AgreementNumPayments', blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementupfrontpayments = models.SmallIntegerField(db_column='AgreementUpfrontPayments', blank=True,
                                                        null=True)  # Field name made lowercase.
    agreementpaymentfrequency = models.SmallIntegerField(db_column='AgreementPaymentFrequency', blank=True,
                                                         null=True)  # Field name made lowercase.
    agreementpenaltyintrdueday = models.SmallIntegerField(db_column='AgreementPenaltyIntrDueDay', blank=True,
                                                          null=True)  # Field name made lowercase.
    agreementpenaltyinterestcode = models.SmallIntegerField(db_column='AgreementPenaltyInterestCode', blank=True,
                                                            null=True)  # Field name made lowercase.
    agreementagreementtypeid = models.ForeignKey('go_agreement_definitions', on_delete=models.DO_NOTHING,
                                                 db_column='AgreementAgreementTypeID', blank=True, null=True,
                                                 to_field="agreementdefid")  # Field name made lowercase.
    agreementdefname = models.CharField(db_column='AgreementDefName', max_length=200, blank=True,
                                        null=True)  # Field name made lowercase.
    agreementcollectiontype = models.SmallIntegerField(db_column='AgreementCollectionType', blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementregulated = models.SmallIntegerField(db_column='AgreementRegulated', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementfinancecompanycode = models.SmallIntegerField(db_column='AgreementFinanceCompanyCode', blank=True,
                                                           null=True)  # Field name made lowercase.
    agreementdebitinterestcode = models.SmallIntegerField(db_column='AgreementDebitInterestCode', blank=True,
                                                          null=True)  # Field name made lowercase.
    agreementhpistatus = models.SmallIntegerField(db_column='AgreementHPIStatus', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementdueday = models.SmallIntegerField(db_column='AgreementDueDay', blank=True,
                                               null=True)  # Field name made lowercase.
    agreementarrearsletter = models.SmallIntegerField(db_column='AgreementArrearsLetter', blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementgenericpersontype = models.SmallIntegerField(db_column='AgreementGenericPersonType', blank=True,
                                                          null=True)  # Field name made lowercase.
    agreementexperianhpistatus = models.SmallIntegerField(db_column='AgreementExperianHPIStatus', blank=True,
                                                          null=True)  # Field name made lowercase.
    agreementincomeassessment = models.SmallIntegerField(db_column='AgreementIncomeAssessment', blank=True,
                                                         null=True)  # Field name made lowercase.
    agreementsectionofmonth = models.SmallIntegerField(db_column='AgreementSectionOfMonth', blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementdayofweek = models.SmallIntegerField(db_column='AgreementDayOfWeek', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementautocolldeposit = models.SmallIntegerField(db_column='AgreementAutoCollDeposit', blank=True,
                                                        null=True)  # Field name made lowercase.
    agreementdiscountrate = models.SmallIntegerField(db_column='AgreementDiscountRate', blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementproposalid = models.IntegerField(db_column='AgreementProposalID', blank=True,
                                              null=True)  # Field name made lowercase.
    agreementsettledflag = models.NullBooleanField(db_column='AgreementSettledFlag', blank=True,
                                               null=True)  # Field name made lowercase.
    agreementseasonalpayments = models.NullBooleanField(db_column='AgreementSeasonalPayments', blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementarrearsfrozen = models.NullBooleanField(db_column='AgreementArrearsFrozen', blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementletterprinted = models.NullBooleanField(db_column='AgreementLetterPrinted', blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementposted = models.NullBooleanField(db_column='AgreementPosted', blank=True,
                                          null=True)  # Field name made lowercase.
    agreementignoreletter = models.NullBooleanField(db_column='AgreementIgnoreLetter', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementuserecurringins = models.NullBooleanField(db_column='AgreementUseRecurringIns', blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementpayoutcomplete = models.NullBooleanField(db_column='AgreementPayoutComplete', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementintrratelocked = models.NullBooleanField(db_column='AgreementIntrRateLocked', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementautocpdone = models.NullBooleanField(db_column='AgreementAutoCPDone', blank=True,
                                              null=True)  # Field name made lowercase.
    agreementexperianclosed = models.NullBooleanField(db_column='AgreementExperianClosed', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementautocollectintronly = models.NullBooleanField(db_column='AgreementAutoCollectIntrOnly', blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementexported = models.NullBooleanField(db_column='AgreementExported', blank=True,
                                            null=True)  # Field name made lowercase.
    agreementmanualintervention = models.NullBooleanField(db_column='AgreementManualIntervention', blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementmonthlyinvoice = models.NullBooleanField(db_column='AgreementMonthlyInvoice', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementexportexclude = models.NullBooleanField(db_column='AgreementExportExclude', blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementupfrontautocollected = models.NullBooleanField(db_column='AgreementUpfrontAutoCollected', blank=True,
                                                        null=True)  # Field name made lowercase.
    agreementstoppenaltyintr = models.NullBooleanField(db_column='AgreementStopPenaltyIntr', blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementnoinvoice = models.NullBooleanField(db_column='AgreementNoInvoice', blank=True,
                                             null=True)  # Field name made lowercase.
    agreementdlrannualfeeignored = models.NullBooleanField(db_column='AgreementDlrAnnualFeeIgnored', blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementrefixpaylock = models.NullBooleanField(db_column='AgreementRefixPayLock', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementpayadvanceio = models.NullBooleanField(db_column='AgreementPayAdvanceIO', blank=True,
                                                null=True)  # Field name made lowercase.
    agreementregularpayment = models.NullBooleanField(db_column='AgreementRegularPayment', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementccd = models.NullBooleanField(db_column='AgreementCCD', blank=True,
                                       null=True)  # Field name made lowercase.
    agreementbaddebtposted = models.NullBooleanField(db_column='AgreementBadDebtPosted', blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementmemorandum = models.TextField(db_column='AgreementMemorandum', blank=True,
                                           null=True)  # Field name made lowercase.
    agreementprevnumber = models.TextField(db_column='AgreementPrevNumber', blank=True,
                                           null=True)  # Field name made lowercase. This field type is a guess.
    agreementarrearshistory = models.TextField(db_column='AgreementArrearsHistory', blank=True,
                                               null=True)  # Field name made lowercase. This field type is a guess.
    agreementseasonalmonths = models.TextField(db_column='AgreementSeasonalMonths', blank=True,
                                               null=True)  # Field name made lowercase. This field type is a guess.
    agreementeir = models.FloatField(db_column='AgreementEIR', blank=True, null=True)  # Field name made lowercase.
    agreementpersoncommission = models.DecimalField(db_column='AgreementPersonCommission', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementpersoncommissionvat = models.DecimalField(db_column='AgreementPersonCommissionVat', max_digits=19,
                                                       decimal_places=4, blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementsalesmancommissionvat = models.DecimalField(db_column='AgreementSalesmanCommissionVat', max_digits=19,
                                                         decimal_places=4, blank=True,
                                                         null=True)  # Field name made lowercase.
    agreementwarningflag = models.CharField(db_column='AgreementWarningFlag', max_length=2, blank=True,
                                            null=True)  # Field name made lowercase.
    agreementpayouttrantypeid = models.SmallIntegerField(db_column='AgreementPayoutTranTypeID', blank=True,
                                                         null=True)  # Field name made lowercase.
    agreementwarningtext = models.CharField(db_column='AgreementWarningText', max_length=255, blank=True,
                                            null=True)  # Field name made lowercase.
    agreementtransmatchreference = models.CharField(db_column='AgreementTransMatchReference', max_length=50,
                                                    blank=True, null=True)  # Field name made lowercase.
    agreementfunderid = models.SmallIntegerField(db_column='AgreementFunderID', blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementpreviousfunderid = models.SmallIntegerField(db_column='AgreementPreviousFunderID', blank=True,
                                                         null=True)  # Field name made lowercase.
    agreementcapitalisedcomm = models.DecimalField(db_column='AgreementCapitalisedComm', max_digits=19,
                                                   decimal_places=4, blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementfunderchangereason = models.CharField(db_column='AgreementFunderChangeReason', max_length=50,
                                                   blank=True, null=True)  # Field name made lowercase.
    agreementsettlementreason = models.CharField(db_column='AgreementSettlementReason', max_length=50, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementprofitloss = models.DecimalField(db_column='AgreementProfitLoss', max_digits=19, decimal_places=4,
                                              blank=True, null=True)  # Field name made lowercase.
    agreementuseprofitloss = models.NullBooleanField(db_column='AgreementUseProfitLoss', blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementacpdefaultcustomer = models.CharField(db_column='AgreementACPDefaultCustomer', max_length=4,
                                                   blank=True, null=True)  # Field name made lowercase.
    agreementnorefund = models.NullBooleanField(db_column='AgreementNoRefund', blank=True,
                                            null=True)  # Field name made lowercase.
    agreementdisableccp = models.NullBooleanField(db_column='AgreementDisableCCP', blank=True,
                                              null=True)  # Field name made lowercase.
    agreementbankiban = models.CharField(db_column='AgreementBankIBAN', max_length=34, blank=True,
                                         null=True)  # Field name made lowercase.
    agreementpenintrmaxdays = models.SmallIntegerField(db_column='AgreementPenIntrMaxDays', blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementfundingsource = models.CharField(db_column='AgreementFundingSource', max_length=50, blank=True,
                                              null=True)  # Field name made lowercase.
    agreementexternalreferenceno4 = models.CharField(db_column='AgreementExternalReferenceNo4', max_length=50,
                                                     blank=True, null=True)  # Field name made lowercase.
    agreementexternalreferenceno5 = models.CharField(db_column='AgreementExternalReferenceNo5', max_length=50,
                                                     blank=True, null=True)  # Field name made lowercase.
    agreementaccruedinteresttd = models.DecimalField(db_column='AgreementAccruedInterestTD', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementdaysinarrears = models.DecimalField(db_column='AgreementDaysInArrears', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementp2pfeecommmargin = models.DecimalField(db_column='AgreementP2PFeeCommMargin', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementnpvrateuplift = models.DecimalField(db_column='AgreementNPVRateUplift', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementworkingdays = models.SmallIntegerField(db_column='AgreementWorkingDays', blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementicbsubmitdate = models.DateTimeField(db_column='AgreementICBSubmitDate', blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementacquisproductcode = models.CharField(db_column='AgreementACQUISProductCode', max_length=7, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementletterprinteduser = models.CharField(db_column='AgreementLetterPrintedUser', max_length=25, blank=True,
                                                  null=True)  # Field name made lowercase.
    agreementpayoutdeferreddate = models.DateTimeField(db_column='AgreementPayoutDeferredDate', blank=True,
                                                       null=True)  # Field name made lowercase.
    agreementbankbic = models.CharField(db_column='AgreementBankBIC', max_length=11, blank=True,
                                        null=True)  # Field name made lowercase.
    agreementgaugescore = models.SmallIntegerField(db_column='AgreementGaugeScore', blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementsettlementsubreason = models.CharField(db_column='AgreementSettlementSubReason', max_length=50,
                                                    blank=True, null=True)  # Field name made lowercase.
    agreementproducttierid = models.IntegerField(db_column='AgreementProductTierID', blank=True,
                                                 null=True)  # Field name made lowercase.
    agreementexpectedinstalment = models.DecimalField(db_column='AgreementExpectedInstalment', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementcpaconsentrevoked = models.NullBooleanField(db_column='AgreementCPAConsentRevoked', blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementstopaccrualintr = models.NullBooleanField(db_column='AgreementStopAccrualIntr', blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementhierarchyrate = models.SmallIntegerField(db_column='AgreementHierarchyRate', blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementunutilisedcreditrate = models.DecimalField(db_column='AgreementUnutilisedCreditRate', max_digits=19,
                                                        decimal_places=4, blank=True,
                                                        null=True)  # Field name made lowercase.
    agreementrefixaddnper = models.SmallIntegerField(db_column='AgreementRefixAddNPer', blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementcontractenddate = models.DateTimeField(db_column='AgreementContractEndDate', blank=True,
                                                    null=True)  # Field name made lowercase.
    agreementaltergoodsagreementnumber = models.CharField(db_column='AgreementAlterGoodsAgreementNumber',
                                                          max_length=10, blank=True,
                                                          null=True)  # Field name made lowercase.
    agreementstopduextracalc = models.NullBooleanField(db_column='AgreementStopDUExtraCalc', blank=True,
                                                   null=True)  # Field name made lowercase.
    agreementgenericperson7number = models.CharField(db_column='AgreementGenericPerson7Number', max_length=10,
                                                     blank=True, null=True)  # Field name made lowercase.
    agreementgenericperson8number = models.CharField(db_column='AgreementGenericPerson8Number', max_length=10,
                                                     blank=True, null=True)  # Field name made lowercase.
    agreementgenericperson9number = models.CharField(db_column='AgreementGenericPerson9Number', max_length=10,
                                                     blank=True, null=True)  # Field name made lowercase.
    agreementshadowinterestrate = models.DecimalField(db_column='AgreementShadowInterestRate', max_digits=19,
                                                      decimal_places=4, blank=True,
                                                      null=True)  # Field name made lowercase.
    agreementshadowinteresttd = models.DecimalField(db_column='AgreementShadowInterestTD', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    assetfinancenetadvance = models.DecimalField(db_column='AssetFinanceNetAdvance', max_digits=19,
                                                 decimal_places=4, blank=True,
                                                 null=True)  # Field name made lowercase.
    assetfinanceinputvat = models.DecimalField(db_column='AssetFinanceInputVAT', max_digits=19, decimal_places=4,
                                               blank=True, null=True)  # Field name made lowercase.
    assetfinanceinputvrt = models.DecimalField(db_column='AssetFinanceInputVRT', max_digits=19, decimal_places=4,
                                               blank=True, null=True)  # Field name made lowercase.
    assetfinancetotaltaxinput = models.DecimalField(db_column='AssetFinanceTotalTAXInput', max_digits=19,
                                                    decimal_places=4, blank=True,
                                                    null=True)  # Field name made lowercase.
    assetfinancetotalfinancedamount = models.DecimalField(db_column='AssetFinanceTotalFinancedAmount',
                                                          max_digits=19, decimal_places=4, blank=True,
                                                          null=True)  # Field name made lowercase.
    assetfinancetotalassetcost = models.DecimalField(db_column='AssetFinanceTotalAssetCost', max_digits=19,
                                                     decimal_places=4, blank=True,
                                                     null=True)  # Field name made lowercase.
    agreementclosedflag = models.ForeignKey('core.ncf_applicationwide_text', on_delete=models.CASCADE,
                                                 blank=True, null=True,
                                                 to_field="app_text_code")
    agreementddstatus = models.ForeignKey('core.ncf_dd_status_text', on_delete=models.CASCADE,
                                          blank=True, null=True,
                                          to_field="dd_text_code")
    closeddate = models.DateTimeField(db_column='ClosedDate', blank=True, null=True)
    agreement_stage = models.CharField(db_column='agreement_stage', max_length=34, blank=True,
                                         null=True)  # Field name made lowercase.
    agreement_closed_reason = models.CharField(max_length=250, null=True)

    class Meta:
        ordering = ('agreement_stage','-agreementagreementdate','-agreementnumber')
        verbose_name = 'Agreement Query Detail'
        verbose_name_plural = 'Agreement Query Details'

    def __str__(self):
        return '{}'.format(self.agreementnumber)


class go_account_transaction_detail(models.Model):

    go_id = models.ForeignKey('go_agreement_index', max_length=50, null=True, on_delete=models.DO_NOTHING)
    agreementnumber = models.CharField(max_length=10, null=True, db_column='AgreementNumber', default='')
    transactiondate = models.DateTimeField(db_column='TransDate', blank=True, null=True)
    transactionsourceid = models.CharField(db_column='TransactionSourceId', max_length=10)
    transtypeid = models.SmallIntegerField(db_column='TransTypeID', blank=True, null=True)
    transtypedesc = models.CharField(db_column='TransTypeDescription', max_length=100, blank=True, null=True)
    transflag = models.CharField(db_column='TransFlag', max_length=3, blank=True, null=True)
    transfallendue = models.NullBooleanField(db_column='TransFallenDue', blank=True, null=True)
    transnetpayment = models.DecimalField(db_column='TransNetPayment', max_digits=19, decimal_places=4, blank=True, null=True)
    transvatpayment = models.DecimalField(db_column='TransVatPayment', max_digits=19, decimal_places=4, blank=True,
                                          null=True)
    transgrosspayment = models.DecimalField(db_column='TransGrossPayment', max_digits=19, decimal_places=4, blank=True,
                                            null=True)
    transpayproid = models.IntegerField(db_column='TransPayProID', blank=True, null=True)
    transpayproprincipal = models.DecimalField(db_column='TransPayProPrincipal', max_digits=19, decimal_places=4,
                                               blank=True,
                                               null=True)  # Field name made lowercase.
    transpayprointerest = models.DecimalField(db_column='TransPayProInterest', max_digits=19, decimal_places=4,
                                              blank=True,
                                              null=True)  # Field name made lowercase.
    # TODO : PAF Changes - Start
    transactionpaymentmethod = models.CharField(max_length=15, null=True, default='')
    transaction_detail_unique = models.SmallIntegerField(blank=True, null=True)
    # TODO : PAF Changes - End

    class Meta:
        verbose_name = 'Account Transaction Detail'
        verbose_name_plural = 'Account Transactions Details'

    def __str__(self):
        return '{}'.format(self.agreementnumber)


class go_account_transaction_summary(models.Model):
    go_id = models.ForeignKey('go_agreement_index', max_length=50, null=True, on_delete=models.DO_NOTHING)

    #agreementnumber = models.CharField(db_column='AgreementNumber', max_length=10, blank=True, null=True)
    agreementnumber = models.CharField(max_length=10,  null=True, db_column='AgreementNumber', default='')
    transactiondate = models.DateTimeField(db_column='TransDate', blank=True, null=True)
    transactionsourceid = models.CharField(db_column='TransactionSourceId', max_length=10)
    transactionsourcedesc = models.CharField(db_column='TransactionSourceDesc', max_length=20, blank=True, null=True)
    transtypeid = models.SmallIntegerField(db_column='TransTypeID', blank=True, null=True)
    transtypedesc = models.CharField(db_column='TransTypeDescription', max_length=100, blank=True, null=True)
    transflag = models.CharField(db_column='TransFlag', max_length=3, blank=True, null=True)
    transfallendue = models.NullBooleanField(db_column='TransFallenDue', blank=True, null=True)
    transnetpayment = models.DecimalField(db_column='TransNetPayment', max_digits=19, decimal_places=4, blank=True, null=True)
    transgrosspayment = models.DecimalField(db_column='TransGrossPayment', max_digits=19, decimal_places=4, blank=True,
                                          null=True)
    transrunningtotal = models.DecimalField(db_column='TransRunningTotal', max_digits=19, decimal_places=4, blank=True, null=True)
    transagreementcustomernumber = models.ForeignKey('go_customers', db_column='TransAgreementCustomerNumber',
                                                max_length=10, blank=True, null=True, to_field="customernumber",
                                                on_delete=models.CASCADE)  # Field name made lowercase.
    transcustomercompany = models.CharField(db_column='TransCustomerCompany', max_length=60, blank=True,
                                       null=True)  # Field name made lowercase.
    transagreementclosedflag = models.ForeignKey('core.ncf_applicationwide_text', on_delete=models.CASCADE,
                                            blank=True, null=True,
                                            to_field="app_text_code")
    transagreementddstatus = models.ForeignKey('core.ncf_dd_status_text', on_delete=models.CASCADE,
                                          blank=True, null=True,
                                          to_field="dd_text_code")
    transagreementcloseddate = models.DateTimeField(db_column='TransClosedDate', blank=True, null=True)
    transagreementdefname = models.CharField(db_column='TransAgreementDefName', max_length=200, blank=True,
                                        null=True)  # Field name made lowercase.
    transagreementagreementdate = models.DateTimeField(db_column='TransAgreementAgreementDate', blank=True,
                                                  null=True)  # Field name made lowercase.
    transddpayment = models.NullBooleanField(default=True, blank=True, null=True)
    transagreementauthority = models.CharField(db_column='TransAgreementAuthority', max_length=30, blank=True,
                                          null=True)  # Field name made lowercase.
    transnetpaymentinterest = models.DecimalField(db_column='TransNetPaymentInterest', max_digits=19, decimal_places=4, blank=True, null=True)
    transnetpaymentcapital = models.DecimalField(db_column='TransNetPaymentCapital', max_digits=19, decimal_places=4, blank=True, null=True)
    transactionbatch_id = models.CharField(max_length=50,  null=True, db_column='TransactionBatch_id', default='')
    transactionstatus = models.CharField(max_length=15,  null=True, default='')
    # TODO: PAF Changes - Start
    transactionpaymentmethod = models.CharField(max_length=15,  null=True, default='')
    transaction_summary_unique = models.SmallIntegerField(blank=True, null=True)
    # TODO: PAF Changes - End

    class Meta:
        verbose_name = 'Account Transaction Summary'
        verbose_name_plural = 'Account Transactions Summary'

    def __str__(self):
        return '{}'.format(self.agreementnumber)


class go_profile_types(models.Model):

    profile_type = models.SmallIntegerField(db_column='ProfileType', blank=True, null=True)  # Field name made lowercase.
    profile_description = models.CharField(db_column='ProfileDescription', max_length=50, blank=True, null=True)  # Field name made lowercase.
    selectable = models.NullBooleanField(db_column='selectable', blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.profile_description)


class go_broker(models.Model):

    broker_type = models.SmallIntegerField(db_column='ProfileType', blank=True, null=True)  # Field name made lowercase.
    broker_description = models.CharField(db_column='ProfileDescription', max_length=50, blank=True, null=True)  # Field name made lowercase.
    selectable = models.NullBooleanField()

    def __str__(self):
        return '{}'.format(self.broker_description)


class go_funder(models.Model):

    PROVIDER_CHOICES = (
        ('datacash', 'datacash'),
        ('eazycollect', 'eazycollect')
    )

    funder_code = models.SmallIntegerField(blank=True, null=True)  # Field name made lowercase.
    funder_description = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase.
    funder_SUN = models.CharField(max_length=50, blank=True, null=True)  # Field name made lowercase.
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, null=True, blank=True)
    selectable = models.NullBooleanField()
    batch_prefix = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.funder_description)


class go_agreement_id_definitions(models.Model):

    agreement_definitions = models.ForeignKey('go_agreement_definitions', null=True, blank=True,
                                              on_delete=models.DO_NOTHING)
    # TODO: PAF Changes - Start
    profile_type = models.ForeignKey('go_profile_types', null=True, blank=True, to_field='id',
                                     on_delete=models.DO_NOTHING)

    # profile_type = models.IntegerField(blank=True, null=True)
    # # TODO: PAF Changes - End
    broker = models.ForeignKey(go_broker, null=True, blank=True, to_field='id',
                                on_delete=models.DO_NOTHING)

    prepend = models.CharField(max_length=50, blank=True, null=True)

    append = models.CharField(max_length=50, blank=True, null=True)

    min_length = models.IntegerField(blank=True, null=True)

    max_length = models.IntegerField(blank=True, null=True)

    allow_digits = models.NullBooleanField(default=True)

    allow_letters = models.NullBooleanField(default=True)

    allow_characters = models.NullBooleanField(default=True)

    disallowed_characters = models.CharField(null=True, blank=True, max_length=50)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

# TODO: PAF Changes - Start
class go_selectable_functionality(models.Model):

    function = models.CharField(max_length=50, blank=True, null=True)
    customer = models.CharField(max_length=50, blank=True, null=True)
    agreement_type = models.IntegerField(blank=True, null=True)
    funder = models.IntegerField(blank=True, null=True)
    broker = models.IntegerField(blank=True, null=True)
    option1 = models.IntegerField(blank=True, null=True)
    option2 = models.IntegerField(blank=True, null=True)
    selectable = models.IntegerField(blank=True, null=True)
    visible = models.IntegerField(blank=True, null=True)
    selectable_value = models.IntegerField(blank=True, null=True)
    hidden_value = models.IntegerField(blank=True, null=True)

class agreement_number_validation(models.Model):

    customer = models.CharField(max_length=50, blank=True, null=True)
    agreement_type = models.IntegerField(blank=True, null=True)
    funder = models.IntegerField(blank=True, null=True)
    broker = models.IntegerField(blank=True, null=True)
    prepend = models.CharField(max_length=50, blank=True, null=True)
    append = models.CharField(max_length=50, blank=True, null=True)
    min_length = models.IntegerField(blank=True, null=True)
    max_length = models.IntegerField(blank=True, null=True)
    allow_digits = models.NullBooleanField(default=True)
    allow_letters = models.NullBooleanField(default=True)
    allow_characters = models.NullBooleanField(default=True)
    disallowed_characters = models.CharField(null=True, blank=True, max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class go_collection_schedule(models.Model):

    collection_schedule = models.SmallIntegerField(blank=True, null=True)
    collection_description = models.CharField(max_length=50, blank=True, null=True)
    selectable = models.NullBooleanField(blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.collection_description)

class go_payment_method(models.Model):

    payment_method = models.SmallIntegerField(blank=True, null=True)
    payment_method_description = models.CharField(max_length=50, blank=True, null=True)
    payment_method_group = models.CharField(max_length=50, blank=True, null=True)
    selectable = models.NullBooleanField(blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.payment_method_description)
# TODO: PAF Changes - End

class transition_log(models.Model):

    agreementnumber = models.CharField(max_length=10, null=True, db_column='AgreementNumber', default='')

    transition_date = models.DateTimeField(auto_now_add=True)

    from_system = models.CharField(null=True, blank=True, max_length=50)

    to_system = models.CharField(null=True, blank=True, max_length=50)
