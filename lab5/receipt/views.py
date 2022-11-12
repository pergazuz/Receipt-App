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
    return render(request, 'receipt/receipt.html', data)

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

class ReceiptList(View):
    def get(self, request):
        receipts = list(Receipt.objects.order_by('receipt_no').all().values())
        data = dict()
        data['receipts'] = receipts

        return JsonResponse(data)

class ReceiptDetail(View):
    def get(self, request, pk, pk2):

        receipt_no = pk + '/' + pk2

        receipt = list(Receipt.objects.select_related('customer_code')
            .filter(receipt_no=receipt_no)
            .values('receipt_no', 'date', 'customer_code', 'payment_method', 'payment_reference'
            , 'total_received', 'remarks'))
        receiptlineitem = list(ReceiptLineItem.objects.select_related('product_code')
            .filter(receipt_no=receipt_no)
            .values('receipt_no', 'item_no', 'invoice_no', 'amount_paid_here'))

        data = dict()
        data['receipt'] = receipt
        data['receiptlineitem'] = receiptlineitem

        return JsonResponse(data)

class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = '__all__'

class LineItemForm(forms.ModelForm):
    class Meta:
        model = ReceiptLineItem
        fields = '__all__'

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptCreate(View): #Check again

    @transaction.atomic
    def post(self, request):
        if Receipt.objects.count() != 0:        # Check Number of Record of Invoice Table == SELECT COUNT(*) FROM invoice
            receipt_no_max = Receipt.objects.aggregate(Max('receipt_no'))['receipt_no__max']    # SELECT MAX(invoice_no) FROM invoice
            receipt_no_temp = [re.findall(r'(\w+?)(\d+)', receipt_no_max)[0]][0]                # Split 'IN100/22' to 'IN' , '100'
            next_receipt_no = receipt_no_temp[0] + str(int(receipt_no_temp[1])+1) + "/22"       # next_invoice_no = 'IN' + '101' + '/22' = 'IN101/22'
        else:
            next_receipt_no = "IN100/22"        # If Number of Record of Invoice = 0 , next_invoice_no = IN100/22
        print(next_receipt_no)
        # Copy POST data and correct data type Ex 1,000.00 -> 1000.00
        request.POST = request.POST.copy()
        request.POST['receipt_no'] = next_receipt_no
        request.POST['date'] = reFormatDateMMDDYYYY(request.POST['date'])
        request.POST['total_received'] = reFormatNumber(request.POST['total_received'])


        data = dict()
        # Insert correct data to invoice
        form = ReceiptForm(request.POST)
        if form.is_valid():
            receipt = form.save()
            
            # Delete all invoice_line_item of invoice_no before loop insert new data
            ReceiptLineItem.objects.filter(receipt_no=next_receipt_no).delete()

            # Read lineitem from ajax and convert to json dictionary
            dict_lineitem = json.loads(request.POST['lineitem'])

            # Loop replace json data with correct data type Ex 1,000.00 -> 1000.00
            for lineitem in dict_lineitem['lineitem']:
                lineitem['receipt_no'] = next_receipt_no
                lineitem['amount_due'] = reFormatNumber(lineitem['amount_due'])
                lineitem['amount_received'] = reFormatNumber(lineitem['amount_received'])

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
            data['receipt'] = model_to_dict(receipt)
        else:
            # if invoice from is not valid return error message
            data['error'] = form.errors
            print (form.errors)

        return JsonResponse(data)

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptUpdate(View):

    @transaction.atomic
    def post(self, request):
        # Get inovice_no from POST data
        receipt_no = request.POST['receipt_no']

        receipt = Receipt.objects.get(receipt_no=receipt_no)
        request.POST = request.POST.copy()
        request.POST['date'] = reFormatDateMMDDYYYY(request.POST['date'])
        request.POST['total_received'] = reFormatNumber(request.POST['total_received'])

        data = dict()
        # instance is object that will be udpated
        form = ReceiptForm(instance=receipt, data=request.POST)
        if form.is_valid():
            receipt = form.save()

            ReceiptLineItem.objects.filter(receipt_no=receipt_no).delete()

            dict_lineitem = json.loads(request.POST['lineitem'])
            for lineitem in dict_lineitem['lineitem']:
                lineitem['receipt_no'] = receipt_no
                lineitem['amount_due'] = reFormatNumber(lineitem['amount_due'])
                lineitem['amount_received'] = reFormatNumber(lineitem['amount_received'])
                formlineitem = LineItemForm(lineitem)
                if formlineitem.is_valid():
                    formlineitem.save()
                else:
                    data['error'] = form.errors
                    transaction.set_rollback(True)

            data['receipt'] = model_to_dict(receipt)
        else:
            data['error'] = form.errors
            print (form.errors)

        return JsonResponse(data)

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptDelete(View):
    def post(self, request):
        receipt_no = request.POST["receipt_no"]

        data = dict()
        receipt = Receipt.objects.get(receipt_no=receipt_no)
        if receipt:
            receipt.delete()
            ReceiptLineItem.objects.filter(receipt_no=receipt_no).delete()
            data['message'] = "Receipt Deleted!"
        else:
            data['error'] = "Error!"

        return JsonResponse(data)

class ReceiptReport(View):
    def get(self, request, pk, pk2):
        receipt_no = pk + "/" + pk2
        receipt = list(Receipt.objects.select_related('customer_code')
            .filter(receipt_no=receipt_no)
            .values('receipt_no', 'date', 'customer_code', 'payment_method', 'payment_reference'
            , 'total_received', 'remarks'))
        receiptlineitem = list(ReceiptLineItem.objects.select_related('product_code')
            .filter(receipt_no=receipt_no)
            .values('receipt_no', 'item_no', 'invoice_no', 'amount_paid_here'))

        data = dict()
        data['receipt'] =receipt[0]
        data['receiptlineitem'] = receiptlineitem
        
        return render(request, 'receipt/report.html', data)

def reFormatDateMMDDYYYY(ddmmyyyy):
        if (ddmmyyyy == ''):
            return ''
        return ddmmyyyy[3:5] + "/" + ddmmyyyy[:2] + "/" + ddmmyyyy[6:]

def reFormatNumber(str):
        if (str == ''):
            return ''
        return str.replace(",", "")