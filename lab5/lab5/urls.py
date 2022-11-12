"""lab5 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from invoice import views
from receipt import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('product/list', views.ProductList.as_view(), name='product_list'),
    path('customer/list', views.CustomerList.as_view(), name='customer_list'),
    path('customer/detail/<customer_code>', views.CustomerDetail.as_view(), name='customer_detail'),

    
    #path('invoice/list', views.InvoiceList.as_view(), name='invoice_list'),
    #path('invoice/detail/<str:pk>/<str:pk2>', views.InvoiceDetail.as_view(), name='invoice_detail'),
    #path('invoice/create', views.InvoiceCreate.as_view(), name='invoice_create'),
    #path('invoice/update', views.InvoiceUpdate.as_view(), name='invoice_update'),
    #path('invoice/delete', views.InvoiceDelete.as_view(), name='invoice_delete'),
    #path('invoice/report/<str:pk>/<str:pk2>', views.InvoiceReport.as_view(), name='invoice_report'),
    

    path('receipt/list', views.ReceiptList.as_view(), name='receipt_list'),
    path('receipt/detail/<str:pk>/<str:pk2>', views.ReceiptDetail.as_view(), name='receipt_detail'),
    path('receipt/create', views.ReceiptCreate.as_view(), name='receipt_create'),
    path('receipt/update', views.ReceiptUpdate.as_view(), name='receipt_update'),
    path('receipt/delete', views.ReceiptDelete.as_view(), name='receipt_delete'),
    path('receipt/report/<str:pk>/<str:pk2>', views.ReceiptReport.as_view(), name='receipt_report'),

]
