from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors

from django.db.models import Sum
import decimal, datetime

from core_agreement_crud.models import  go_agreement_querydetail, \
                                        go_customers, \
                                        go_account_transaction_summary, \
                                        go_account_transaction_detail

class PrintVatStatement:

    def __init__(self, buffer, pagesize, agreement_id, calendar_year, output_version):

        self.buffer = buffer

        if pagesize == 'A4':
            self.pagesize = A4
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

        self.agreement_id = agreement_id
        self.calendar_year = calendar_year
        self.output_version = output_version

    @staticmethod
    def _header_footer(canvas, doc):
        # Save the state of our canvas so we can draw on it
        canvas.saveState()
        styles = getSampleStyleSheet()

        # Header
        # header = Paragraph('This is a multi-line header.  It goes on every page.   ' * 5, styles['Normal'])
        # w, h = header.wrap(doc.width, doc.topMargin)
        header = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
        header.hAlign = 'RIGHT'
        header.drawOn(canvas, 350, doc.height - 50)

        # Footer
        # footer = Paragraph('This is a multi-line footer.  It goes on every page.   ' * 5, styles['Normal'])
        # w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer = Image("static/assets/images/others/bluerock-footer.jpg", width=8.2 * inch, height=1 * inch)
        footer.hAlign = 'RIGHT'
        footer.drawOn(canvas, 12, 50)

        # Release the canvas
        canvas.restoreState()

    def print_users(self):
        buffer = self.buffer
        doc = SimpleDocTemplate(buffer,
                                rightMargin=12,
                                leftMargin=12,
                                topMargin=12,
                                bottomMargin=12,
                                pagesize=self.pagesize)

        # Our container for 'Flowable' objects
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(pdf_buffer)
        flowables = []

        Agreement_Start = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                       transactionsourceid__in=['SP1', 'GO1']).order_by(
            'transactiondate', ).first()
        Agreement_Start_Date = Agreement_Start.transactiondate

        agreement_detail = go_agreement_querydetail.objects.get(agreementnumber=self.agreement_id)
        agreement_customer = go_customers.objects.get(customernumber=agreement_detail.agreementcustomernumber)
        account_detail = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                      transactionsourceid__in=['SP1', 'GO1']).order_by(
            'transactiondate', )
        account_summary = go_account_transaction_summary.objects.filter(agreementnumber=self.agreement_id)
        account_detail_fees = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                           transactionsourceid__in=['SP1', 'GO1'],
                                                                           transtypeid__isnull=False).order_by(
            'transactiondate')
        print(self.calendar_year)
        FROM_DATE = str(self.calendar_year) + '-01-01'
        TO_DATE = str(self.calendar_year) + '-12-31'
        # print(workingdate)
        # FROM_DATE = '2020-01-01'
        # TO_DATE = '2020-12-31'
        account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                              transactionsourceid__in=['SP1', 'GO1'],
                                                                              transtypeid__isnull=True,
                                                                              transactiondate__gte=FROM_DATE,
                                                                              transactiondate__lt=TO_DATE
                                                                              ).order_by('transactiondate')
        count_transactions = account_detail_rentals.count()

        try:
            Rentals2 = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
        except:
            Rentals2 = 0

        try:
            Rentals = account_detail_rentals.aggregate(Sum(account_detail_rentals.transnetpayment))
            if Rentals is not None:
                Rentals += Rentals2[account_detail_rentals.transnetpayment]
        except:
            pass

        # Agreement Type
        if agreement_detail.agreementdefname != 'Hire Purchase' and agreement_detail.agreementdefname != 'Management Fee':
            agreement_type = 'Lease'
            sales_tax_rate = 1.2
        else:
            agreement_type = 'HP'
            sales_tax_rate = 1.0

        # Agreement Payable Net of VAT
        try:
            agreement_payable_net = agreement_detail.agreementoriginalprincipal + agreement_detail.agreementcharges
        except:
            agreement_payable_net = 0

        # Add in Fees if they exist
        try:
            agreement_fees_net = account_detail_fees.aggregate(account_detail_fees.transnetpayment)
            if agreement_fees_net is not None:
                agreement_payable_net += agreement_fees_net[account_detail_fees.transnetpayment]
        except:
            pass

        # Agreement Payable Gross of VAT
        agreement_payable_gross = (agreement_payable_net * decimal.Decimal(sales_tax_rate))

        sample_style_sheet = getSampleStyleSheet()
        sample_style_sheet.list()
        data3 = ("", "")

        first_rental_date = agreement_detail.agreementfirstpaymentdate.strftime("%d/%m/%Y")

        # get Number of Document Fees
        try:
            doc_fee_count = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                         transactionsourceid__in=['SP1', 'GO1'],
                                                                         transactiondate__lt=Agreement_Start_Date).count()
        except:
            doc_fee_count = 0
        # get Number of Primaries
        try:
            primary_count = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                         transactionsourceid__in=['SP1', 'GO1'],
                                                                         transtypeid__isnull=True,
                                                                         transactiondate__gte=Agreement_Start_Date).count()
        except:
            primary_count = 0

        # get Number of Secondaries
        try:
            secondary_count = account_summary.filter(transactionsourceid__in=['SP2', 'SP3', 'GO3']).count()
        except:
            secondary_count = 0

        for row in account_detail:
            row.transvatpayment = row.transnetpayment * decimal.Decimal(0.2)

        agreement_instalment_gross = agreement_detail.agreementinstalmentnet
        if agreement_detail.agreementinstalmentvat is not None:
            agreement_instalment_gross += agreement_detail.agreementinstalmentvat
        if agreement_detail.agreementinstalmentins is not None:
            agreement_instalment_gross += agreement_detail.agreementinstalmentins

        array = []
        # TODO: GO#110 - Start
        TOTAL_NET = 0
        TOTAL_VAT = 0
        TOTAL_GROSS = 0
        # TODO: GO#110 - End
        Manual_Payment = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                      transtypedesc='Documentation Fee',
                                                                      transactionsourceid__in=['SP1', 'GO1'],
                                                                      transactiondate__gte=FROM_DATE,
                                                                      transactiondate__lt=TO_DATE
                                                                      )
        for a in Manual_Payment:
            if a.transactiondate is not None:
                array.append(str((a.transactiondate.strftime("%d/%m/%Y")))), \
                array.append(str("Manual"))
                # array.append(str('£0.00'))
                # array.append(str('£0.00'))
                # TODO: GO#110 - Start
                NET_Column = round(a.transnetpayment, 2)
                TOTAL_NET = TOTAL_NET + NET_Column

                array.append(str("£" + format(NET_Column, ',')))

                Manual_Payment_vat = round(a.transnetpayment * decimal.Decimal(0.2), 2)

                array.append(str("£" + format(Manual_Payment_vat, ','))),
                TOTAL_VAT = TOTAL_VAT + Manual_Payment_vat

                Gross = round(Manual_Payment_vat + a.transnetpayment, 2)
                TOTAL_GROSS = TOTAL_GROSS + Gross
                array.append(str("£" + format(Gross, ','))),

        Doc_Fee_2 = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                 transtypedesc='Documentation Fee 2',
                                                                 transactionsourceid__in=['SP1', 'GO1'],
                                                                 transactiondate__gte=FROM_DATE,
                                                                 transactiondate__lt=TO_DATE
                                                                 )

        for a in Doc_Fee_2:
            if a.transactiondate is not None:
                array.append(str((a.transactiondate.strftime("%d/%m/%Y")))), \
                array.append(str("Manual"))

                NET_Column = round(a.transnetpayment, 2)
                TOTAL_NET = TOTAL_NET + NET_Column
                array.append(str("£" + format(NET_Column, ',')))

                Manual_Payment_vat = round(a.transnetpayment * decimal.Decimal(0.2), 2)
                if agreement_type == "HP":
                    array.append("£0.00")
                    GROSS_Column = round(a.transnetpayment, 2)
                    array.append(str("£" + format(GROSS_Column, ',')))
                    TOTAL_GROSS = TOTAL_GROSS + NET_Column
                else:
                    array.append(str("£" + format(Manual_Payment_vat, ','))),
                    TOTAL_VAT = TOTAL_VAT + Manual_Payment_vat
                    Gross = round(Manual_Payment_vat + a.transnetpayment, 2)
                    array.append(str("£" + format(Gross, ','))),
                    TOTAL_GROSS = TOTAL_GROSS + Gross
        # TODO: GO#110 - End
        for transaction in account_detail_rentals:

            array.append(str((transaction.transactiondate.strftime("%d/%m/%Y")))),
            print(transaction.transactiondate.strftime("%d/%m/%Y"))
            print(Agreement_Start_Date.strftime("%d/%m/%Y"))

            if transaction.transactiondate > Agreement_Start_Date:
                array.append(str("Direct Debit")),
            else:
                array.append(str("Manual")),

            BAMF_fees = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                     transactionsourceid__in=['SP1', 'GO1'],
                                                                     transtypeid__isnull=False,
                                                                     transtypedesc__in=['Bi-Annual Management Fee',
                                                                                        'Bi-Annual Anniversary Fee',
                                                                                        'Annual Management Fee'],
                                                                     transactiondate=transaction.transactiondate).aggregate(
                Sum('transnetpayment'))
            Fees_Correct = BAMF_fees['transnetpayment__sum']
            if Fees_Correct is None: Fees_Correct = decimal.Decimal(0.00)

            Risk_fees = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                     transactionsourceid__in=['SP1', 'GO1'],
                                                                     transtypeid__isnull=False,
                                                                     transtypedesc='Risk Fee',
                                                                     transactiondate=transaction.transactiondate).aggregate(
                Sum('transnetpayment'))
            Risk_Correct = Risk_fees['transnetpayment__sum']
            if Risk_Correct is None: Risk_Correct = decimal.Decimal(0.00)

            account_detail_rentals = go_account_transaction_detail.objects.filter(agreementnumber=self.agreement_id,
                                                                                  transactionsourceid__in=['SP1',
                                                                                                           'GO1'],
                                                                                  transtypeid__isnull=True,
                                                                                  transactiondate=transaction.transactiondate).aggregate(
                Sum('transnetpayment'))

            Rentals_Correct = account_detail_rentals['transnetpayment__sum']
            # TODO: GO#110 Vat Statement Correction 2 - Start
            # if agreement_type == "HP":
            #     Rentals_Correct = round(Rentals_Correct + round((Risk_Correct)*decimal.Decimal(0.833333), 2) +Fees_Correct, 2)
            # else:
            Rentals_Correct = round(Rentals_Correct + Risk_Correct + Fees_Correct, 2)
            if account_detail_rentals['transnetpayment__sum'] is None: Rentals_Correct = decimal.Decimal(0.00)
            array.append(str("£" + format(Rentals_Correct, ','))),
            TOTAL_NET = TOTAL_NET + Rentals_Correct
            Rentals_Correct_vat = round(Rentals_Correct * decimal.Decimal(0.2), 2)
            # TODO: GO#110 Vat Statement Correction 2 - End
            if agreement_type == "HP":
                # TODO: GO#110 Vat Statement Correction 2 - Start
                vat_hp = round((Risk_Correct) * decimal.Decimal(0.2) + (Fees_Correct * decimal.Decimal(0.2)), 2)
                # TODO: GO#110 Vat Statement Correction 2 - End
                array.append(str("£" + format(vat_hp, ','))),
                TOTAL_VAT = TOTAL_VAT + vat_hp
            else:
                array.append(str("£" + format(Rentals_Correct_vat, ','))),
                TOTAL_VAT = TOTAL_VAT + Rentals_Correct_vat

            if agreement_type == "HP":
                installment_total = round(Rentals_Correct + (round(vat_hp, 2)), 2)

            else:
                installment_total = round(Rentals_Correct + Rentals_Correct_vat, 2)

            array.append(str("£" + format(installment_total, ','))),
            TOTAL_GROSS = TOTAL_GROSS + installment_total
            # TODO: GO#110 - End
        n = len(array)
        print(n)
        x = 0
        data3 = []
        # data3.append(['Date', 'Type', 'Net', 'VAT', 'Fee Net', 'Fee VAT', 'Gross'])
        data3.append(['Date', 'Type', 'Net', 'VAT', 'Gross'])
        while x <= n - 1:
            a = x
            b = a + 1
            c = b + 1
            d = c + 1
            e = d + 1
            data3.append([array[a], array[b], array[c], array[d], array[e]])
            x = x + 5

        t3 = Table(data3, colWidths=98, rowHeights=20, style=[('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                                                              ('BOX', (0, 0), (-1, -1), 1, colors.black),
                                                              ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                                              ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
                                                              ])
        # TODO: GO#110 - Start

        b2 = str("£" + format(TOTAL_NET, ','))
        d2 = str("£" + format(round(TOTAL_VAT, 2), ','))
        f2 = str("£" + format(round(TOTAL_GROSS, 2), ','))
        # TODO: GO#110 - End
        a2 = Paragraph("<b>Net:</b>", sample_style_sheet['BodyText'])
        c2 = Paragraph("<b>VAT:</b>", sample_style_sheet['BodyText'])
        e2 = Paragraph("<b>Total:</b>", sample_style_sheet['BodyText'])

        data6 = [
            ['', a2, b2],
            ['', c2, d2],
            ['', e2, f2],
        ]
        t6 = Table(data6, colWidths=225, rowHeights=20, style=[('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                                                               ('BOX', (2, 0), (-1, -1), 1, colors.black),
                                                               ('GRID', (2, 0), (-1, -1), 0.5, colors.black),
                                                               ])

        t6._argW[0] = 4.08 * inch
        t6._argW[1] = 1.36 * inch
        t6._argW[2] = 1.36 * inch

        paragraph_2 = Paragraph(
            "<b>Frequency:</b> Monthly"
            ,
            sample_style_sheet['BodyText']
        )

        data10 = [["This invoice has been issued for VAT purposes only and is not a demand for payment."],
                  ["VAT can only be recovered by you after each payment has been made."],
                  ["VAT Reg No.974594073"],
                  ["You will receive these VAT schedules annually over the primary term of your agreement."]]

        paragraph_2.hAlign = 'CENTRE'

        # im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
        # im = Image("static/assets/images/others/bluerock-blank-spacer-logo.jpg", width=3.4 * inch, height=0.8 * inch)
        im = Image("static/assets/images/others/bluerock-logo.jpg", width=3.4 * inch, height=0.8 * inch)
        im.hAlign = 'RIGHT'

        if agreement_customer.customeraddress1:
            address1 = Paragraph(agreement_customer.customeraddress1, sample_style_sheet['BodyText'])
        else:
            address1 = ''
        if agreement_customer.customeraddress2:
            address2 = Paragraph(agreement_customer.customeraddress2, sample_style_sheet['BodyText'])
        else:
            address2 = ''
        if agreement_customer.customeraddress3:
            address3 = Paragraph(agreement_customer.customeraddress3, sample_style_sheet['BodyText'])
        else:
            address3 = ''
        if agreement_customer.customeraddress4:
            address4 = Paragraph(agreement_customer.customeraddress4, sample_style_sheet['BodyText'])
        else:
            address4 = ''
        if agreement_customer.customeraddress5:
            address5 = Paragraph(agreement_customer.customeraddress5, sample_style_sheet['BodyText'])
        else:
            address5 = ''
        if agreement_customer.customerpostcode:
            postcode = Paragraph(agreement_customer.customerpostcode, sample_style_sheet['BodyText'])
        array = [agreement_customer.customercompany, address1, address2, address3, address4, address5, postcode]
        while ('' in array): array.remove('')
        array.append('')
        array.append('')
        array.append('')
        array.append('')
        array.append('')

        data2 = [
            [array[0], ''],
            # ['', '', ''],
            [array[1], ''],
            [array[2], ''],
            [array[3], ''],
            [array[4], ''],
            [array[5], ''],
            [array[6], ''],
        ]

        t2 = Table(data2, colWidths=163.5, rowHeights=15, style=[('BOX', (0, 0), (-2, -1), 1, colors.black),
                                                                 ])
        t2._argW[0] = 5.4 * inch
        t2._argW[1] = 1.4 * inch
        # t2._argW[2] = 1.4 * inch

        c3 = Paragraph("Agreement Date:", sample_style_sheet['Heading4'])
        d3 = Paragraph(str(Agreement_Start_Date.strftime("%d/%m/%Y")), sample_style_sheet['BodyText'])
        e3 = Paragraph("Frequency:", sample_style_sheet['Heading4'])
        f3 = Paragraph("Monthly", sample_style_sheet['BodyText'])
        g3 = Paragraph("Agreement:", sample_style_sheet['Heading4'])
        h3 = Paragraph(self.agreement_id, sample_style_sheet['BodyText'])
        i3 = Paragraph("Term:", sample_style_sheet['Heading4'])
        j3 = Paragraph(str(primary_count), sample_style_sheet['BodyText'])

        data7 = [[c3, d3, i3, j3, e3, f3, ""],
                 [g3, h3, ""],
                 ]
        t7 = Table(data7, colWidths=100, rowHeights=15, style=[
            ('BOX', (0, 0), (-2, -1), 1, colors.black),
            ('BOX', (0, 0), (0, -1), .5, colors.black),
            ('GRID', (0, 0), (-2, -2), 0.5, colors.black),
        ])

        t7._argW[0] = 1.4 * inch
        t7._argW[1] = 0.9 * inch
        t7._argW[2] = 0.8 * inch
        t7._argW[3] = 0.5 * inch
        t7._argW[4] = 1.0 * inch
        t7._argW[5] = 0.8 * inch
        t7._argW[6] = 1.4 * inch

        data8 = [["", "VAT SCHEDULE", ""], ]

        t8 = Table(data8, colWidths=163.5, rowHeights=25, style=[('BOX', (0, 0), (-1, -1), 1, colors.black),
                                                                 ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                                                                 ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')
                                                                 ])

        t10 = Table(data10, colWidths=500, rowHeights=15, style=[('ALIGN', (0, 0), (-1, -1), 'CENTRE')])

        paragraph_4 = Paragraph(
            " "
            ,
            sample_style_sheet['BodyText']
        )

        flowables.append(Spacer(1,1.2*inch))
        flowables.append(t2)
        flowables.append(paragraph_4)
        flowables.append(t7)
        flowables.append(paragraph_4)
        flowables.append(t8)
        flowables.append(t3)
        flowables.append(t6)
        flowables.append(Spacer(1, 0.15 * inch))
        flowables.append(t10)

        if self.output_version == 'PDF':
            doc.build(flowables, onFirstPage=self._header_footer, onLaterPages=self._header_footer,
                      canvasmaker=NumberedCanvas)
        else:
            doc.build(flowables)

        # Get the value of the BytesIO buffer and write it to the response.
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            # self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    # def draw_page_number(self, page_count):
    #     # Change the position of this to wherever you want the page number to be
    #     self.drawRightString(211 * mm, 15 * mm + (0.2 * inch),
    #                          "Page %d of %d" % (self._pageNumber, page_count))
