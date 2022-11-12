
var ROW_NUMBER = 5;

$(document).ready( function () {

    /* set up text box inovice data to datepicker, it popup calendar after click text box */
    $("#txt_InvoiceDate").datepicker({ 
        dateFormat: 'dd/mm/yy' 
    });
    
    /* When click button calendar, call datepicker show, it popup calendar after click  button */
    $('#btn_InvoiceDate').click(function() {
        $('#txt_InvoiceDate').datepicker('show');
    });

    /* Add one row to table (in last row), When click button '+' in header of table */
    $('.table-add').click(function () {
        // Copy hidden row of table and clear hidden class
        var clone = $('#div_table').find('tr.hide').clone(true).removeClass('hide table-line');
        // Append copyed row to body of table, add to last row
        $('#div_table').find('tbody').append(clone);
        // Call re_order_no to set item_no
        re_order_no();
    });

    /* Delete row after click 'X' in last column */
    $('.table-remove').click(function () {
        $(this).parents('tr').detach();         // Delete that table row (TR) and all table data (TD)

        // Check number of row, if number of row < 9 then add one row
        // 9 = default row (5) + header (1) + footer (3)
        if ($('#table_main tr').length <= (ROW_NUMBER + 1 + 3)) {   
            add_last_one_row();
        }
        re_order_no();                          // Call re_order_no to re-order item_no (order_no)
        re_calculate_total_price();             // Call re_calculate_total_price to calculate  total_price, vat, amount_due
    });

    /* Check input on table are corrected format, if not correct use last value */
    $('table').on('focusin', 'td[contenteditable]', function() {
        $(this).data('val', $(this).html());                    // keep value in table before change
    }).on('keypress', 'td[contenteditable]', function (e) {
        if (e.keyCode == 13) {
            return false;
        }
    }).on('focusout', 'td[contenteditable]', function() {
        var prev = $(this).data('val');                         // get last keep value in table after change
        var data = $(this).html();                              // get changed value
        if (!numberRegex.test(data)) {                          // check changed value correct format Ex 1,000.00
            $(this).text(prev);                                 // if format not correct use last keep value
        } else {
            $(this).data('val', $(this).html());                // if format correct keep this value are last value
        }
        re_calculate_total_price();                             // Call re_calculate_total_price to calculate  total_price, vat, amount_due
    });

    /* Get Customer Name when type in text box customer code */
    $('#txt_CustomerCode').change (function () {
        var customer_code = $(this).val().trim();       // get customer_code from text box

        $.ajax({                                        // call backend /customer/detail/<customer_code>
            url:  '/customer/detail/' + customer_code,
            type:  'get',
            dataType:  'json',
            success: function  (data) {
                if (data.customers.length > 0) {        // check data not empty customer
                    $('#txt_CustomerCode').val(data.customers[0].customer_code);    // put to text box
                    $('#txt_CustomerName').val(data.customers[0].name);             // put to text box (label)
                } else {
                    $('#txt_CustomerName').val('');    // if can't find customer_name, reset text box
                }
            },
            error: function (xhr, status, error) {
                $('#txt_CustomerName').val('');         // if something error, reset text box
            }
        });
    });

    /* Load customer list to Modal and show popup */
    /* when click button magnifying glass after Customer Code */
    $('.search_customer_code').click(function () {
        $.ajax({
            url:  '/customer/list',                     // call backend /customer/list
            type:  'get',
            dataType:  'json',
            success: function  (data) {
                let rows =  '';
                var i = 1;
                data.customers.forEach(customer => {    // loop each result of customers to create table rows
                    rows += `
                    <tr>
                        <td>${i++}</td>
                        <td><a class='a_click' href='#'>${customer.customer_code}</a></td>
                        <td>${customer.name}</td>
                        <td></td>
                        <td class='hide'></td>
                    </tr>`;
                });
                $('#table_modal > tbody').html(rows);   // set new table rows to table body (tbody) of popup

                $('#model_header_1').text('Customer Code');     // set header of popup
                $('#model_header_2').text('Customer Name');
                $('#model_header_3').text('Note');

                $('#txt_modal_param').val('customer_code');     // mark customer_code for check after close modal
                $('#modal_form').modal();                       // open popup (modal)
            },
        });        
    });

    /* search product code, load product list to Modal and show popup */
    /* when click button magnifying glass after Product Code in table */
    $('.search_product_code').click(function () {
        $(this).parents('tr').find('.order_no').html('*');  // mark row number with '*' for return value after close modal

        $.ajax({                                        // call backend /product/list
            url:  '/product/list',
            type:  'get',
            dataType:  'json',
            success: function  (data) {
                let rows =  '';
                var i = 1;
                data.products.forEach(product => {       // loop each result of products to create table rows
                    rows += `
                    <tr>
                        <td>${i++}</td>
                        <td><a class='a_click' href='#'>${product.code}</a></td>
                        <td>${product.name}</td>
                        <td>${formatNumber(product.units)}</td>
                        <td class='hide'></td>
                    </tr>`;
                });
                $('#table_modal > tbody').html(rows);       // set new table rows to table body (tbody) of popup

                $('#model_header_1').text('Product Code');      // set header of popup
                $('#model_header_2').text('Product Name');
                $('#model_header_3').text('Unit Price');

                
                $('#txt_modal_param').val('product_code');      // mark product_code for check after close modal
                $('#modal_form').modal();                       // open popup
            },
        });
    });

    // After click link in Model (popup), Return value of product_code, customer_code, invoice_no to main form
    $('body').on('click', 'a.a_click', function() {
        var code = $(this).parents('tr').find('td:nth-child(2)').children().html();
        var name = $(this).parents('tr').find('td:nth-child(3)').html();
        var note = $(this).parents('tr').find('td:nth-child(4)').html();
        var option = $(this).parents('tr').find('td:nth-child(5)').html();

        if ($('#txt_modal_param').val() == 'product_code') {
            // Loop each in data table
            $("#table_main tbody tr").each(function() {
                // Return data in row number = * (jquery mark * before popup (modal) )
                if ($(this).find('.order_no').html() == '*') {
                    // return selected product detail (code,name,units) to table row
                    $(this).find('.project_code_1 > span').html(code);
                    $(this).find('.product_name').html(name);
                    $(this).find('.unit_price').html(note);
                    $(this).find('.quantity').html("1");           // default quantiy is '1'
                }
            });
            
            re_calculate_total_price();
        } else if ($('#txt_modal_param').val() == 'customer_code') {
            $('#txt_CustomerCode').val(code);
            $('#txt_CustomerName').val(name);
        } else if ($('#txt_modal_param').val() == 'invoice_no') {
            $('#txt_InvoiceNo').val(code);
            $('#txt_InvoiceDate').val(name);
            $('#txt_CustomerCode').val(note);
            $('#txt_CustomerCode').change();

            get_invoice_detail(code);
        }

        $('#modal_form').modal('toggle');               // close modal
    });

    // detect modal form closed, call re_order_no
    $('#modal_form').on('hidden.bs.modal', function () {
        re_order_no();
    });

    /* Click button 'NEW', reset form */
    $('#btnNew').click(function () {
        reset_form();
    });


    /* Click button 'EDIT', load invoice list to modal */
    $('#btnEdit').click(function () {
        $.ajax({                                        // call backend /invoice/list
            url:  '/invoice/list',
            type:  'get',
            dataType:  'json',
            success: function  (data) {
                let rows =  '';
                var i = 1;
                data.invoices.forEach(invoice => {      // loop each result of invoices to create table rows
                    var invoice_date = invoice.date;
                    // Change format date from 01-12-2022 -> 01/12/2022
                    invoice_date = invoice_date.slice(0,10).split('-').reverse().join('/');
                    rows += `
                    <tr>
                        <td>${i++}</td>
                        <td><a class='a_click' href='#'>${invoice.invoice_no}</a></td>
                        <td>${invoice_date}</td>
                        <td>${invoice.customer_code_id}</td>
                        <td class='hide'></td>
                    </tr>`;
                });
                $('#table_modal > tbody').html(rows);      // set new table rows to table body (tbody) of popup

                $('#model_header_1').text('Invoice No');    // set header of popup
                $('#model_header_2').text('Invoice Date');
                $('#model_header_3').text('Customer Code');

                $('#txt_modal_param').val('invoice_no');    // mark invoice_no for check after close modal
                $('#modal_form').modal();                   // open popup
            },
        });        
    });

    /* Click button 'SAVE', call /invoice/create or /invoice/update */
    $('#btnSave').click(function () {
        var customer_code = $('#txt_CustomerName').val().trim();    // get customer_code from text box
        if (customer_code == '') {                                  // check customer_code is empty
            alert('กรุณาระบุ Customer');
            $('#txt_CustomerCode').focus();
            return false;
        }
        var invoice_date = $('#txt_InvoiceDate').val().trim();      // get invoice data from text box
        if (!dateRegex.test(invoice_date)) {                        // check invoice data is correct format DD/MM/YYYY
            alert('กรุณาระบุวันที่ ให้ถูกต้อง');
            $('#txt_InvoiceDate').focus();
            return false;
        }
        if ($('#txt_InvoiceNo').val() == '<new>') {                 // check invoice no in form, if invoice no = <new> then call create otherwise call update
            var token = $('[name=csrfmiddlewaretoken]').val();      // get django security code
                  
            $.ajax({                                                // call backend /invoice/create
                url:  '/invoice/create',
                type:  'post',
                data: $('#form_invoice').serialize() + "&lineitem=" +lineitem_to_json(),
                headers: { "X-CSRFToken": token },
                dataType:  'json',
                success: function  (data) {
                    if (data.error) {                               // if backend return error message, log it
                        console.log(data.error);
                        alert('การบันทึกล้มเหลว');
                    } else {
                        $('#txt_InvoiceNo').val(data.invoice.invoice_no)    // SAVE success, show new invoice no
                        alert('บันทึกสำเร็จ');
                    }                    
                },
            });  
        } else {
            var token = $('[name=csrfmiddlewaretoken]').val();      // get django security code

            $.ajax({                                                // call backend /invoice/update
                url:  '/invoice/update',
                type:  'post',
                data: $('#form_invoice').serialize() + "&lineitem=" +lineitem_to_json() + "&invoice_no=" + $('#txt_InvoiceNo').val(),
                headers: { "X-CSRFToken": token },
                dataType:  'json',
                success: function  (data) {
                    if (data.error) {                           // if backend return error message, log it
                        console.log(data.error);
                        alert('การบันทึกล้มเหลว');
                    } else {            
                        alert('บันทึกสำเร็จ');                      // SAVE success, show popup message
                    }
                },
            }); 
        }
    });

    /* Click button 'DELETE', call backend /invoice/delete */
    $('#btnDelete').click(function () {
        if ($('#txt_InvoiceNo').val() == '<new>') {
            alert ('ไม่สามารถลบ Invoice ใหม่ได้');
            return false;
        }
        if (confirm ("คุณต้องการลบ Invoice No : '" + $('#txt_InvoiceNo').val() + "' ")) {
            console.log('Delete ' + $('#txt_InvoiceNo').val());
            var token = $('[name=csrfmiddlewaretoken]').val();          // get django security code
            $.ajax({                                                    // call backend /invoice/delete
                url:  '/invoice/delete',
                data: 'invoice_no=' + $('#txt_InvoiceNo').val(),
                type:  'post',
                headers: { "X-CSRFToken": token },
                dataType:  'json',
                success: function  (data) {
                    reset_form();                                       // after delete success call reset_form
                },
            });            
        }
    });

    /* Click button 'PRINT', open new tab of browser with /invoice/reprot/<invpoce_no> */
    $('#btnPrint').click(function () {
        if ($('#txt_InvoiceNo').val() == '<new>') {
            return false;
        }
        window.open('/invoice/report/' + $('#txt_InvoiceNo').val());
    });

    /* Start from */
    reset_form ();
});

/* read all data inside table and convert to json string */
/* return json string of line item (all data inside table) */
function lineitem_to_json () {
    var rows = [];                                                  // create empty array 'rows'
    var i = 0;
    $("#table_main tbody tr").each(function(index) {                // loop each table data
        if ($(this).find('.project_code_1 > span').html() != '') {  // check row have data
            rows[i] = {};                                           // create empty object in rows[index]
            rows[i]["item_no"] = (i+1);                             // copy data from table row to variable 'rows'
            rows[i]["product_code"] = $(this).find('.project_code_1 > span').html();
            rows[i]["product_name"] = $(this).find('.product_name').html();
            rows[i]["unit_price"] = $(this).find('.unit_price').html();
            rows[i]["quantity"] = $(this).find('.quantity').html();
            rows[i]["extended_price"] = $(this).find('.extended_price').html();
            i++;
        }
    });
    var obj = {};                                                   // create empty object
    obj.lineitem = rows;                                            // assign 'rows' to object.lineitem
    //console.log(JSON.stringify(obj));

    return JSON.stringify(obj);                                     // return object in JSON format
}

/* get invoice detail from backend with invoice_no and fill to the form */
function get_invoice_detail (invoice_no) {
    $.ajax({                                                            // call backend /invoice/detail/IN100/22
        url:  '/invoice/detail/' + encodeURIComponent(invoice_no),
        type:  'get',
        dataType:  'json',
        success: function  (data) {
            console.log(data);

            reset_table();                                              // reset table
            for(var i=ROW_NUMBER;i<data.invoicelineitem.length;i++) {   // generate row by number of result
                add_last_one_row();
            }
            var i = 0;
            $("#table_main tbody tr").each(function() {                 // fill result data to each row
                if (i < data.invoicelineitem.length) {
                    $(this).find('.project_code_1 > span').html(data.invoicelineitem[i].product_code);
                    $(this).find('.product_name').html(data.invoicelineitem[i].product_code__name);
                    $(this).find('.unit_price').html(data.invoicelineitem[i].unit_price);
                    $(this).find('.quantity').html(data.invoicelineitem[i].quantity);
                }
                i++;
            });
            re_calculate_total_price();                                 // re-calculate total_price, vat, amount due
        },
    });
}

/* Loop each data table and calculate extended_price, total_price, vat, amount due */
function re_calculate_total_price () {
    var total_price = 0;

    // Loop each in Data Table
    $("#table_main tbody tr").each(function() {
        //get product_code from Table Row in Table
        var product_code = $(this).find('.project_code_1 > span').html().trim();
        //console.log (product_code);
        if (product_code != '') {
            var unit_price = $(this).find('.unit_price').html().replace(/,/g, '');
            $(this).find('.unit_price').html(formatNumber((unit_price)));
            var quantity = $(this).find('.quantity').html();
            $(this).find('.quantity').html(parseInt(quantity));
        
            var extended_price = unit_price * quantity;
            $(this).find('.extended_price').html(formatNumber(extended_price));
            total_price += extended_price;
        }
    });

    $('#lbl_TotalPrice').text(formatNumber(total_price));
    $('#txt_TotalPrice').val($('#lbl_TotalPrice').text());
    $('#lbl_VAT').text(formatNumber(total_price * 0.07));
    $('#txt_VAT').val($('#lbl_VAT').text());
    $('#lbl_AmountDue').text(formatNumber(total_price * 1.07));
    $('#txt_AmountDue').val($('#lbl_AmountDue').text());
}

/* Reset form to original form */
function reset_form() {
    $('#txt_InvoiceNo').attr("disabled", "disabled");
    $('#txt_InvoiceNo').val('<new>');

    reset_table();
    
    $('#txt_InvoiceDate').val(new Date().toJSON().slice(0,10).split('-').reverse().join('/'));

    $('#txt_CustomerCode').val('');
    $('#txt_CustomerName').val('');

    $('#lbl_TotalPrice').text('0.00');
    $('#lbl_VAT').text('0.00');
    $('#lbl_AmountDue').text('0.00');
}

/* Reset Table to original from */
function reset_table() {
    $('#table_main > tbody').html('');          // Clear body of table (tbody), table will remain header and footer
    for(var i=1; i<= ROW_NUMBER; i++) {         // Loop 5 times
        add_last_one_row()                      // Add one row to table
    }    
}

/* Add one row to table */
function add_last_one_row () {
    $('.table-add').click();                    // Call event click of button '+' in header of table, for add one row
}

/* Reorder number item_no (order_no) on table */
function re_order_no () {
    var order_number = 1;
    // Loop each data table
    $("#table_main tbody tr").each(function() {         
        // set order number to column order_no
        $(this).find('.order_no').html(order_number);   
        order_number++;
    });
}

/* Format input to display number 2 floating point Ex 1,000.00 */
function formatNumber (num) {
    if (num === '') return '';
    num = parseFloat(num); 
    return num.toFixed(2).toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1,");
}

/* Check n is integer */
function isInt(n){
    return Number(n) === n && n % 1 === 0;
}

/* Check n is floating point */
function isFloat(n){
    return Number(n) === n && n % 1 !== 0;
}

/* Pattern for check input is Date format DD/MM/YYYY */
var dateRegex = /^(?=\d)(?:(?:31(?!.(?:0?[2469]|11))|(?:30|29)(?!.0?2)|29(?=.0?2.(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00)))(?:\x20|$))|(?:2[0-8]|1\d|0?[1-9]))([-.\/])(?:1[012]|0?[1-9])\1(?:1[6-9]|[2-9]\d)?\d\d(?:(?=\x20\d)\x20|$))?(((0?[1-9]|1[012])(:[0-5]\d){0,2}(\x20[AP]M))|([01]\d|2[0-3])(:[0-5]\d){1,2})?$/;
//var numberRegex = /^-?\d+\.?\d*$/;

/* Pattern for check input is Money format 1,000.00 */
var numberRegex = /^-?\d*\.?\d*$/

// A few jQuery helpers for exporting only
jQuery.fn.pop = [].pop;
jQuery.fn.shift = [].shift;

