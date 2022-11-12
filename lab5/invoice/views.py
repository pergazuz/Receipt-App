from django.shortcuts import render
from django.http import HttpResponse

from django.views.generic import View
from django.http import JsonResponse
from django import forms
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.forms.models import model_to_dict
from django.db.models import Max
from django.db import transaction
from .models import *
import json
import re

# Create your views here.
def index(request):
    data = {}
    return render(request, 'invoice/index.html', data)

class ProductList(View):
    def get(self, request):
        products = list(Product.objects.all().values())
        data = dict()
        data['products'] = products

        return JsonResponse(data)

class CustomerList(View):
    def get(self, request):
        customers = list(Customer.objects.all().values())
        data = dict()
        data['customers'] = customers

        return JsonResponse(data)

class CustomerDetail(View):
    def get(self, request, customer_code):
        customer = list(Customer.objects.filter(customer_code=customer_code).values())
        data = dict()
        data['customers'] = customer

        return JsonResponse(data)

class InvoiceList(View):
    def get(self, request):
        invoices = list(Invoice.objects.order_by('invoice_no').all().values())
        data = dict()
        data['invoices'] = invoices

        return JsonResponse(data)

class InvoiceDetail(View):
    def get(self, request, pk, pk2):

        invoice_no = pk + '/' + pk2

        invoice = list(Invoice.objects.select_related('customer_code')
            .filter(invoice_no=invoice_no)
            .values('invoice_no', 'date', 'customer_code', 'customer_code__name', 'due_date'
            , 'total', 'vat', 'amount_due'))
        invoicelineitem = list(InvoiceLineItem.objects.select_related('product_code')
            .filter(invoice_no=invoice_no)
            .values('invoice_no', 'item_no', 'product_code', 'product_code__name', 'unit_price'
            , 'quantity', 'product_total'))

        data = dict()
        data['invoice'] = invoice
        data['invoicelineitem'] = invoicelineitem

        return JsonResponse(data)

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = '__all__'

class LineItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceLineItem
        fields = '__all__'

@method_decorator(csrf_exempt, name='dispatch')
class InvoiceCreate(View):

    @transaction.atomic
    def post(self, request):
        if Invoice.objects.count() != 0:        # Check Number of Record of Invoice Table == SELECT COUNT(*) FROM invoice
            invoice_no_max = Invoice.objects.aggregate(Max('invoice_no'))['invoice_no__max']    # SELECT MAX(invoice_no) FROM invoice
            invoice_no_temp = [re.findall(r'(\w+?)(\d+)', invoice_no_max)[0]][0]                # Split 'IN100/22' to 'IN' , '100'
            next_invoice_no = invoice_no_temp[0] + str(int(invoice_no_temp[1])+1) + "/22"       # next_invoice_no = 'IN' + '101' + '/22' = 'IN101/22'
        else:
            next_invoice_no = "IN100/22"        # If Number of Record of Invoice = 0 , next_invoice_no = IN100/22
        print(next_invoice_no)
        # Copy POST data and correct data type Ex 1,000.00 -> 1000.00
        request.POST = request.POST.copy()
        request.POST['invoice_no'] = next_invoice_no
        request.POST['date'] = reFormatDateMMDDYYYY(request.POST['date'])
        request.POST['due_date'] = reFormatDateMMDDYYYY(request.POST['due_date'])
        request.POST['total'] = reFormatNumber(request.POST['total'])
        request.POST['vat'] = reFormatNumber(request.POST['vat'])
        request.POST['amount_due'] = reFormatNumber(request.POST['amount_due'])

        data = dict()
        # Insert correct data to invoice
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            
            # Delete all invoice_line_item of invoice_no before loop insert new data
            InvoiceLineItem.objects.filter(invoice_no=next_invoice_no).delete()

            # Read lineitem from ajax and convert to json dictionary
            dict_lineitem = json.loads(request.POST['lineitem'])

            # Loop replace json data with correct data type Ex 1,000.00 -> 1000.00
            for lineitem in dict_lineitem['lineitem']:
                lineitem['invoice_no'] = next_invoice_no
                lineitem['unit_price'] = reFormatNumber(lineitem['unit_price'])
                lineitem['quantity'] = reFormatNumber(lineitem['quantity'])
                lineitem['product_total'] = reFormatNumber(lineitem['extended_price'])

                # Insert correct data to invoice_line_item
                formlineitem = LineItemForm(lineitem)
                try:
                    formlineitem.save()
                except :
                    # Check something error to show and rollback transaction both invoice and invoice_line_item table
                    data['error'] = formlineitem.errors
                    print (formlineitem.errors)
                    transaction.set_rollback(True)

            # if insert invoice and invoice_line_item success, return invoice data to caller
            data['invoice'] = model_to_dict(invoice)
        else:
            # if invoice from is not valid return error message
            data['error'] = form.errors
            print (form.errors)

        return JsonResponse(data)

@method_decorator(csrf_exempt, name='dispatch')
class InvoiceUpdate(View):

    @transaction.atomic
    def post(self, request):
        # Get inovice_no from POST data
        invoice_no = request.POST['invoice_no']

        invoice = Invoice.objects.get(invoice_no=invoice_no)
        request.POST = request.POST.copy()
        request.POST['date'] = reFormatDateMMDDYYYY(request.POST['date'])
        request.POST['due_date'] = reFormatDateMMDDYYYY(request.POST['due_date'])
        request.POST['total'] = reFormatNumber(request.POST['total'])
        request.POST['vat'] = reFormatNumber(request.POST['vat'])
        request.POST['amount_due'] = reFormatNumber(request.POST['amount_due'])

        data = dict()
        # instance is object that will be udpated
        form = InvoiceForm(instance=invoice, data=request.POST)
        if form.is_valid():
            invoice = form.save()

            InvoiceLineItem.objects.filter(invoice_no=invoice_no).delete()

            dict_lineitem = json.loads(request.POST['lineitem'])
            for lineitem in dict_lineitem['lineitem']:
                lineitem['invoice_no'] = invoice_no
                lineitem['unit_price'] = reFormatNumber(lineitem['unit_price'])
                lineitem['quantity'] = reFormatNumber(lineitem['quantity'])
                lineitem['product_total'] = reFormatNumber(lineitem['extended_price'])
                formlineitem = LineItemForm(lineitem)
                if formlineitem.is_valid():
                    formlineitem.save()
                else:
                    data['error'] = form.errors
                    transaction.set_rollback(True)

            data['invoice'] = model_to_dict(invoice)
        else:
            data['error'] = form.errors
            print (form.errors)

        return JsonResponse(data)

@method_decorator(csrf_exempt, name='dispatch')
class InvoiceDelete(View):
    def post(self, request):
        invoice_no = request.POST["invoice_no"]

        data = dict()
        invoice = Invoice.objects.get(invoice_no=invoice_no)
        if invoice:
            invoice.delete()
            InvoiceLineItem.objects.filter(invoice_no=invoice_no).delete()
            data['message'] = "Invoice Deleted!"
        else:
            data['error'] = "Error!"

        return JsonResponse(data)

class InvoiceReport(View):
    def get(self, request, pk, pk2):
        invoice_no = pk + "/" + pk2
        invoice = list(Invoice.objects.filter(invoice_no=invoice_no)
            .values('invoice_no', 'date', 'customer_code', 'customer_code__name', 'due_date'
            , 'total', 'vat', 'amount_due'))
        invoicelineitem = list(InvoiceLineItem.objects.select_related('product_code')
            .filter(invoice_no=invoice_no)
            .values('invoice_no', 'item_no', 'product_code', 'product_code__name', 'unit_price'
            , 'quantity', 'product_total'))

        data = dict()
        data['invoice'] =invoice[0]
        data['invoicelineitem'] = invoicelineitem
        
        return render(request, 'invoice/report.html', data)

def reFormatDateMMDDYYYY(ddmmyyyy):
        if (ddmmyyyy == ''):
            return ''
        return ddmmyyyy[3:5] + "/" + ddmmyyyy[:2] + "/" + ddmmyyyy[6:]

def reFormatNumber(str):
        if (str == ''):
            return ''
        return str.replace(",", "")