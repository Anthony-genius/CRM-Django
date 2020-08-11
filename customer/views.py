import json
import requests, bs4, re, time

from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.storage import FileSystemStorage
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from urllib.request import urlopen

from customer.models import (AppData, CreditCard, Customer, ElectricPower,
                             File, Lead, Payment, Requirement, RoofType,
                             ServiceNote, Storey, Supplier, BookImageScrap)


@login_required
def home(request):
    """Renders home page with default select options"""

    customer_fields = {
        'from': True,
        'assign': False,
        'agm': False,
        'date_signed': False,
        'customer_name': True,
        'customer_address': False,
        'customer_email': False,
        'phone_number': True,
        'notes': False
    }
    service_fields = {
        'agm': True,
        'customer_name': True,
        'customer_address': True,
        'customer_email': True,
        'phone_number': True,
        'installation_date': True,
        'installer': False,
        'service_note': True
    }
    required_fields = {
        'customer_fields': customer_fields,
        'service_fields': service_fields
    }
    context = {
        'leads': Lead.objects.all(),
        'sales_people': get_user_model().objects.filter(profile__title='salesman'),
        'installers': get_user_model().objects.filter(profile__title='installer'),
        'current_tab': 'home-tab',
        'required_fields': required_fields,
        'scrap_url_fields': True,
    }
    return render(request, 'customer/home.html', context=context)


@login_required
def update_app_data(request):
    print(request.POST)
    if AppData.objects.filter(name=request.POST.get('app_data_name')).exists():
        app_data = AppData.objects.get(name=request.POST.get('app_data_name'))
        app_data.value = request.POST.get('app_data_value')
    else:
        app_data = AppData(name=request.POST.get(
            'app_data_name'), value=request.POST.get('app_data_value'))

    app_data.save()
    return JsonResponse(json.dumps({'message': '{} updated'.format(request.POST.get('app_data_name'))}), safe=False)


@login_required
def save_service_note(request):
    """Save or update a service note linked to a Requirement. All args are contained in resquest form. Returns a JSON data.

    Args:
        requirement_pk: Requirement ID.
        service_note_pk: Optional. Service note ID. If provided, it updated fields of service note, if not, the method creates a new service note.
        content: Service note content.

    Returns:
        message: String to display to the user.
        html: HTML of the table of service notes to reload table.
    """

    if request.method == 'POST':

        if request.POST.get('service_note_pk'):
            # if service note id is provided, load existing service note
            message = 'updated'
            service_note = ServiceNote.objects.get(
                pk=request.POST.get('service_note_pk'))
        else:
            # if service notes id is not provided, create a new service note
            message = 'saved'
            service_note = ServiceNote()

        # set service notes fields
        service_note.requirement_id = request.POST.get('requirement_pk')
        service_note.content = request.POST.get(
            'service_notes') if request.POST.get('service_notes') else None

        # save service note
        service_note.save()

        # load all service notes of the requirement
        service_notes = ServiceNote.objects.filter(
            requirement_id=request.POST.get('requirement_pk'))

        # pre render table to be updated in HTML
        html = render_to_string(
            'customer/service-notes-list.html', context={'service_notes': service_notes})

        return JsonResponse(json.dumps({'message': 'Note {}'.format(message), 'service_notes_list_html': html}),
                            safe=False)


@login_required
def delete_service_note(request):
    """Delete a service note. All args are contained in resquest form. Returns a JSON data.

    Args:
        requirement_pk: Requirement ID.
        service_note_pk: Optional. Service note ID. If provided, it updated fields of service note, if not, the method creates a new service note.

    Returns:
        message: String to display to the user.
        html: HTML of the table of service notes to reload table.
    """

    if request.method == 'POST':
        # load existing service note
        service_note = ServiceNote.objects.get(
            pk=request.POST.get('service_note_pk'))
        service_note.delete()

        # load all service notes of the requirement
        service_notes = ServiceNote.objects.filter(
            requirement_id=request.POST.get('requirement_pk'))

        # pre render table to be updated in HTML
        html = render_to_string(
            'customer/service-notes-list.html', context={'service_notes': service_notes})

        return JsonResponse(json.dumps({'message': 'Note deleted', 'service_notes_list_html': html}), safe=False)


@login_required
def save_supplier(request):
    """Save or update a supplier linked to a Requirement. All args are contained in resquest form. Returns a JSON data.

    Args:
        requirement_pk: Requirement ID.
        supplier_pk: Optional. Supplier ID. If provided, it updated fields of supplier, if not, the method creates a new supplier.
        supplier_name: Supplier name.
        supplier_invoice: Supplier invoice.
        supplier_amount: Supplier paid amount.
        supplier_date_paid: Supplier payment date.

    Returns:
        message: String to display to the user.
        html: HTML of the table of suppliers to reload table.
    """

    if request.method == 'POST':

        if request.POST.get('supplier_pk'):
            # if supplier id is provided, load existing supplier
            message = 'updated'
            supplier = Supplier.objects.get(pk=request.POST.get('supplier_pk'))
        else:
            # if supplier id is not provided, create a new supplier
            message = 'saved'
            supplier = Supplier()

        # set supplier fields
        supplier.requirement_id = request.POST.get('requirement_pk')
        supplier.supplier_name = request.POST.get(
            'supplier_name') if request.POST.get('supplier_name') else None
        supplier.supplier_invoice = request.POST.get(
            'supplier_invoice') if request.POST.get('supplier_invoice') else None
        supplier.supplier_amount = request.POST.get(
            'supplier_amount') if request.POST.get('supplier_amount') else None
        supplier.supplier_date_paid = datetime.strptime(request.POST.get(
            'supplier_date_paid'), '%d/%m/%Y').strftime('%Y-%m-%d') if request.POST.get('supplier_date_paid') else None
        supplier.supplier_notes = request.POST.get(
            'supplier_notes') if request.POST.get('supplier_notes') else None

        # save supplier
        supplier.save()

        # load all suppliers of the requirement
        suppliers = Supplier.objects.filter(
            requirement_id=request.POST.get('requirement_pk'))

        # pre render table to be updated in HTML
        html = render_to_string(
            'customer/supplier-list.html', context={'suppliers': suppliers})

        return JsonResponse(json.dumps(
            {'message': '{} {}'.format(request.POST.get('supplier_name'), message), 'supplier_list_html': html}),
            safe=False)


@login_required
def delete_supplier(request):
    """Delete a supplier. All args are contained in resquest form. Returns a JSON data.

    Args:
        requirement_pk: Requirement ID.
        supplier_pk: Optional. Supplier ID. If provided, it updated fields of supplier, if not, the method creates a new supplier.

    Returns:
        message: String to display to the user.
        html: HTML of the table of suppliers to reload table.
    """

    if request.method == 'POST':
        # load existing supplier
        supplier = Supplier.objects.get(pk=request.POST.get('supplier_pk'))
        supplier.delete()
        message = 'deleted'

        # load all suppliers of the requirement
        suppliers = Supplier.objects.filter(
            requirement_id=request.POST.get('requirement_pk'))

        # pre render table to be updated in HTML
        html = render_to_string(
            'customer/supplier-list.html', context={'suppliers': suppliers})

        return JsonResponse(json.dumps(
            {'message': '{} {}'.format(request.POST.get('supplier_name'), message), 'supplier_list_html': html}),
            safe=False)


@login_required
def upload_file(request):
    """Upload a file and create File model linked to Customer. All args are contained in resquest form. Returns a JSON data.

    Args:
        file: File to upload.

    Returns:
        message: String to display to the user.
        html: HTML of the table of files uploaded.
    """

    if request.method == 'POST':
        # get file from request and store it in disk
        file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        uploaded_file_url = fs.url(filename)

        # create File model for the uploaded file
        file_model = File(customer_id=request.POST.get(
            'customer_id'), file_name=request.POST.get('file_name'), url=uploaded_file_url)

        file_model.save()

        # pre render table to be updated in HTML
        html = render_to_string('customer/file-list.html', context={'files': File.objects.filter(
            customer_id=request.POST.get('customer_id'))}, request=request)

        return JsonResponse(
            json.dumps({'message': 'File {} uploaded'.format(
                request.POST.get('file_name')), 'file_list_html': html}),
            safe=False)


@login_required
def requirement(request):
    """update all information submitted in customer form. Supplier and File upload are not contained in this endpoint"""
    if request.method == 'POST':
        # Fetch customer data
        customer = Customer.objects.get(id=request.POST.get('pk'))

        if 'btn_delete' in request.POST:
            # Delete the current customer and all his data
            customer.delete()
            messages.warning(request, 'Customer {} was deleted.'.format(
                customer.customer_name))

        else:
            # Fetch requirement and credit card data
            requirement = Requirement.objects.filter(
                customer_id=customer.id).first()
            credit_card = CreditCard.objects.filter(
                customer_id=customer.id).first()

            # Update any customer field from form
            customer.leads_from_id = request.POST.get('leads_from') if request.POST.get(
                'leads_from') else None if 'leads_from' in request.POST else customer.leads_from_id
            customer.sales_person_id = request.POST.get('sales_person') if request.POST.get(
                'sales_person') else None if 'sales_person' in request.POST else customer.sales_person_id
            customer.agm = request.POST.get('agm') if request.POST.get(
                'agm') else None if 'agm' in request.POST else customer.agm
            customer.date_signed = datetime.strptime(request.POST.get('date_signed'), '%d/%m/%Y').strftime(
                '%Y-%m-%d') if request.POST.get(
                'date_signed') else None if 'date_signed' in request.POST else customer.date_signed
            customer.customer_name = request.POST.get('customer_name') if request.POST.get(
                'customer_name') else None if 'customer_name' in request.POST else customer.customer_name
            customer.customer_address = request.POST.get('customer_address') if request.POST.get(
                'customer_address') else None if 'customer_address' in request.POST else customer.customer_address
            customer.customer_email = request.POST.get('customer_email') if request.POST.get(
                'customer_email') else None if 'customer_email' in request.POST else customer.customer_email
            customer.phone_number = request.POST.get('phone_number') if request.POST.get(
                'phone_number') else None if 'phone_number' in request.POST else customer.phone_number
            customer.follow_up = request.POST.get('follow_up') if request.POST.get(
                'follow_up') else None if 'follow_up' in request.POST else customer.follow_up
            customer.customer_notes = request.POST.get('customer_notes') if request.POST.get(
                'customer_notes') else None if 'customer_notes' in request.POST else customer.customer_notes
            customer.customer_check = True if request.POST.get(
                'customer_check') else False

            customer.save()

            # Update requirement field from form
            requirement.kw = request.POST.get('kw') if request.POST.get(
                'kw') else None if 'kw' in request.POST else requirement.kw
            requirement.panel = request.POST.get('panel') if request.POST.get(
                'panel') else None if 'panel' in request.POST else requirement.panel
            requirement.panel_pcs = request.POST.get('panel_pcs') if request.POST.get(
                'panel_pcs') else None if 'panel_pcs' in request.POST else requirement.panel_pcs
            requirement.inverter = request.POST.get('inverter') if request.POST.get(
                'inverter') else None if 'inverter' in request.POST else requirement.inverter
            requirement.inverter_pcs = request.POST.get('inverter_pcs') if request.POST.get(
                'inverter_pcs') else None if 'inverter_pcs' in request.POST else requirement.inverter_pcs
            requirement.roof_type_id = request.POST.get('roof_type') if request.POST.get(
                'roof_type') else None if 'roof_type' in request.POST else requirement.roof_type_id
            requirement.storey_id = request.POST.get('storey') if request.POST.get(
                'storey') else None if 'storey' in request.POST else requirement.storey_id
            requirement.electric_power_id = request.POST.get('electric_power') if request.POST.get(
                'electric_power') else None if 'electric_power' in request.POST else requirement.electric_power_id
            requirement.installation_notes = request.POST.get('installation_notes') if request.POST.get(
                'installation_notes') else None if 'installation_notes' in request.POST else requirement.installation_notes
            requirement.extra_amount = request.POST.get('extra_amount') if request.POST.get(
                'extra_amount') else None if 'extra_amount' in request.POST else requirement.extra_amount
            requirement.total_price = request.POST.get('total_price') if request.POST.get(
                'total_price') else None if 'total_price' in request.POST else requirement.total_price
            requirement.deposit_amount = request.POST.get('deposit_amount') if request.POST.get(
                'deposit_amount') else None if 'deposit_amount' in request.POST else requirement.deposit_amount
            requirement.last_amount = request.POST.get('last_amount') if request.POST.get(
                'last_amount') else None if 'last_amount' in request.POST else requirement.last_amount

            requirement.system_price = request.POST.get('system_price') if request.POST.get(
                'system_price') else None if 'system_price' in request.POST else requirement.system_price

            requirement.MNI = request.POST.get('MNI') if request.POST.get(
                'MNI') else None if 'MNI' in request.POST else requirement.MNI

            requirement.finance = True if request.POST.get(
                'finance') else False

            requirement.application = True if request.POST.get(
                'Application') else False

            requirement.installation_date = datetime.strptime(request.POST.get('installation_date'),
                                                              '%d/%m/%Y').strftime(
                '%Y-%m-%d') if request.POST.get(
                'installation_date') else None if 'installation_date' in request.POST else requirement.installation_date
            requirement.installer_id = request.POST.get('installer') if request.POST.get(
                'installer') else None if 'installer' in request.POST else requirement.installer_id

            requirement.installer_date_paid = datetime.strptime(request.POST.get('installer_date_paid'),
                                                                '%d/%m/%Y').strftime('%Y-%m-%d') if request.POST.get(
                'installer_date_paid') else None if 'installer_date_paid' in request.POST else requirement.installer_date_paid

            requirement.installer_amount = request.POST.get('installer_amount') if request.POST.get(
                'installer_amount') else None if 'installer_amount' in request.POST else requirement.installer_amount

            requirement.deposit_date_paid = datetime.strptime(request.POST.get('deposit_date_paid'),
                                                              '%d/%m/%Y').strftime('%Y-%m-%d') if request.POST.get(
                'deposit_date_paid') else None if 'deposit_date_paid' in request.POST else requirement.deposit_date_paid

            requirement.deposit_payment_id = request.POST.get('deposit_payment') if request.POST.get(
                'deposit_payment') else None if 'deposit_payment' in request.POST else requirement.deposit_payment_id

            requirement.unit = request.POST.get('Unit') if request.POST.get(
                'Unit') else None if 'Unit' in request.POST else requirement.unit

            requirement.unit_price = request.POST.get('unit_price') if request.POST.get(
                'unit_price') else None if 'unit_price' in request.POST else requirement.unit_price

            requirement.stc_application = True if request.POST.get(
                'Stc_Application') else False

            requirement.balance_due = datetime.strptime(request.POST.get('Balance_due'), '%d/%m/%Y').strftime(
                '%Y-%m-%d') if request.POST.get(
                'Balance_due') else None if 'Balance_due' in request.POST else requirement.balance_due

            requirement.stc_amount_payment = request.POST.get('STC_Amount_Payment') if request.POST.get(
                'STC_Amount_Payment') else None if 'STC_Amount_Payment' in request.POST else requirement.stc_amount_payment

            requirement.stc_notes = request.POST.get('stc_notes') if request.POST.get(
                'stc_notes') else None if 'stc_notes' in request.POST else requirement.stc_notes

            requirement.stc_amount = request.POST.get('stc_amount') if request.POST.get(
                'stc_amount') else None if 'stc_amount' in request.POST else requirement.stc_amount
            requirement.stc_date_paid = datetime.strptime(request.POST.get('stc_date_paid'), '%d/%m/%Y').strftime(
                '%Y-%m-%d') if request.POST.get(
                'stc_date_paid') else None if 'stc_date_paid' in request.POST else requirement.stc_date_paid
            requirement.STC_PAYMENT = request.POST.get('STC_PAYMENT') if request.POST.get(
                'STC_PAYMENT') else None if 'STC_PAYMENT' in request.POST else requirement.STC_PAYMENT
            requirement.last_amount_paid_date = datetime.strptime(request.POST.get('last_amount_paid_date'),
                                                                  '%d/%m/%Y').strftime(
                '%Y-%m-%d') if request.POST.get(
                'last_amount_paid_date') else None if 'last_amount_paid_date' in request.POST else requirement.last_amount_paid_date

            requirement.last_amount_payment = request.POST.get('last_amount_payment') if request.POST.get(
                'last_amount_payment') else None if 'last_amount_payment' in request.POST else requirement.last_amount_payment

            requirement.last_amount_balance_due = request.POST.get('last_amount_balance_due') if request.POST.get(
                'last_amount_balance_due') else None if 'last_amount_balance_due' in request.POST else requirement.last_amount_balance_due

            requirement.last_amount_payment_method_id = request.POST.get('last_amount_payment_method') if request.POST.get(
                'deposit_payment') else None if 'last_amount_payment_method' in request.POST else requirement.last_amount_payment_method_id

            requirement.last_amount_notes = request.POST.get(
                'last_amount_notes') if request.POST.get(
                'last_amount_notes') else None if 'last_amount_notes' in request.POST else requirement.last_amount_notes

            requirement.power_connection = request.POST.get('power_connection') if request.POST.get(
                'power_connection') else None if 'power_connection' in request.POST else requirement.power_connection
            requirement.meter_connection = request.POST.get('meter_connection') if request.POST.get(
                'meter_connection') else None if 'meter_connection' in request.POST else requirement.meter_connection

            # Check which button was pressed
            if 'btn_already_signed' in request.POST:
                status = 'DEPOSIT'
            elif 'btn_deposit_paid' in request.POST:
                status = 'ON_FILE'
            elif 'btn_payment_order' in request.POST:
                if all([customer.customer_check]):
                    status = 'ORDER'
                else:
                    status = None
                    messages.error(
                        request, 'Customer has to be checked before promoting to order')
            elif 'btn_confirm_all' in request.POST:
                if all([customer.customer_check, requirement.deposit_date_paid]):
                    status = 'INSTALLATION'
                    requirement.order_paid = True
                else:
                    status = None
                    messages.error(
                        request, 'Customer has to be checked and deposit has to be paid before confirming')
            elif 'btn_order_paid' in request.POST:
                if all([requirement.deposit_date_paid]):
                    status = 'INSTALLATION'
                    requirement.order_paid = True
                else:
                    status = None
                    messages.error(
                        request, 'Deposit has to be paid before finishing')
            elif 'btn_finish_installation' in request.POST:
                status = 'ACCOUNT'
                return HttpResponseRedirect('/account')
            elif 'btn_all_paid' in request.POST:
                if all([requirement.deposit_date_paid, requirement.stc_date_paid, requirement.last_amount_paid_date,
                        requirement.suppliers_paid, requirement.installer_date_paid]):
                    status = 'FINISHED'
                else:
                    status = None
                    messages.error(
                        request, 'All amounts have to be paid before finishing')
            elif 'btn_service' in request.POST:
                status = 'SERVICE'
            elif 'btn_delivered' in request.POST:
                status = 'DELIVERED'
            elif 'btn_delivered_home' in request.POST:
                status = 'DELIVERED_HOME'
            elif 'btn_service_home' in request.POST:
                status = 'SERVICE_HOME'
            else:
                status = None

            requirement.status = status if status else requirement.status if requirement.status else None
            requirement.save()

            # Update any credit card field from form
            credit_card.credit_card = request.POST.get('credit_card') if request.POST.get(
                'credit_card') else None if 'credit_card' in request.POST else credit_card.credit_card
            credit_card.expires = datetime.strptime(request.POST.get('expires'), '%m/%Y').strftime(
                '%Y-%m-01') if request.POST.get(
                'expires') else None if 'expires' in request.POST else credit_card.expires

            credit_card.save()

            # Build message to show what was updated
            status_message = ' moved to {}'.format(
                status) if status else ' saved'
            messages.success(request, 'Customer {}{}.'.format(
                request.POST.get('customer_name'), status_message))

        if 'btn_save' in request.POST:
            return redirect(request.META['HTTP_REFERER'])
        else:
            return redirect('home')


@login_required
@permission_required(['customer.customer_list'])
def customer_list(request):
    """POST: Creates a customer and redirects to customer requirement form. GET: Returns List of new customers."""
    if request.method == 'POST':
        # Get data from form
        customer_data = {
            'creator': request.user,
            'leads_from_id': request.POST.get('leads_from'),
            'sales_person_id': request.POST.get('sales_person'),
            'agm': request.POST.get('agm') if request.POST.get('agm') else None,
            'date_signed': datetime.strptime(request.POST.get('date_signed'), '%d/%m/%Y').strftime(
                '%Y-%m-%d') if request.POST.get('date_signed') else None,
            'customer_name': request.POST.get('customer_name'),
            'customer_address': request.POST.get('customer_address'),
            'customer_email': request.POST.get('customer_email'),
            'phone_number': request.POST.get('phone_number'),
            'customer_notes': request.POST.get('customer_notes') if request.POST.get('customer_notes') else None
        }

        requirement_data = {
            'installation_date': datetime.strptime(request.POST.get('installation_date'), '%d/%m/%Y').strftime(
                '%Y-%m-%d') if request.POST.get('installation_date') else None,
            'installer_id': request.POST.get('installer')
        }

        # Create new customer and store it in database
        customer = Customer(**customer_data)
        customer.save()

        if 'btn_create_customer' in request.POST:
            status = 'CREATED'
            path = 'customer-view'
        elif 'btn_create_service' in request.POST:
            status = 'SERVICE_HOME'
            path = 'service-view'

        # Create new requirement and credit card for the new customer
        requirement = Requirement(
            customer=customer, status=status, **requirement_data)
        requirement.save()
        credit_card = CreditCard(customer=customer)
        credit_card.save()

        if request.POST.get('service_note'):
            service_note = ServiceNote(
                requirement=requirement, content=request.POST.get('service_note').strip())
            service_note.save()

        # redirect to new customer view
        return redirect(path, pk=customer.id)

    elif request.method == 'GET':
        # Get all requirements in CREATED status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                status="CREATED").distinct()
        else:
            requirements = Requirement.objects.filter(Q(customer__sales_person=request.user) | Q(
                installer=request.user), status="CREATED").distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Creation Date': 'customer.created_date',
            'Sales': 'customer.sales_person',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Follow Up': 'customer.follow_up',
            'Notes': 'customer.customer_notes',
        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'customer-view',
            'columns': columns,
            'colspan': len(columns)+2,
            'current_tab': 'customer-tab',
            'search_field_visible': True,
            'colspan': len(columns) + 2,
            'current_tab': 'customer-tab'

        }
        # Return requirement list in CREATED status
        return render(request, 'customer/requirement-list.html', context=context)

@login_required
@permission_required(['customer.customer_search'])
def customer_search(request):
    
    if request.method == 'POST':

        # get Search Key data from search form
        search_value = request.POST.get('search_value')
        print("========================")

        # Get all requirements in CREATED status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                status="CREATED").distinct()
        else:
            requirements = Requirement.objects.filter(
                Q(customer__sales_person=request.user) |
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value) | 
                Q(installer=request.user), status="CREATED").distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Creation Date': 'customer.created_date',
            'Sales': 'customer.sales_person',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Follow Up': 'customer.follow_up',
            'Notes': 'customer.customer_notes',
        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'customer-view',
            'columns': columns,
            'colspan': len(columns)+2,
            'current_tab': 'customer-tab',
            'search_field_visible': True,
            'search_value': search_value,
        }

        # Return requirement list in CREATED status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.customer_view'])
def customer_view(request, pk):
    """Returns a customer form in CREATED status"""
    customer = Customer.objects.get(id=pk)

    # Set context.
    # leads, sales_people, roof_types, storeys, electric_powers are default options loaded in Django admin
    # requirement, credit_card, files are loaded from current customer
    # options allow to configure if a section is displayed or not:
    #   follow_up: show follow up input
    #   file_upload_enabled: show file upload form
    #   file_list_enabled: show uploaded files list
    #   installation_data_enabled: show installation data form
    #   customer_check_enabled: show customer check input
    #   deposit_info_enabled: show deposit data form
    #   installer_payment_data_enabled: show installer payment form
    #   supplier_list_enabled: show list of suppliers
    # buttons allow to configure the promotion buttons to display:
    #   btn_promote_name: this is the 'name' attribute of HTML tag
    #   btn_promote_text: this is the content that will be displayed to user
    customer_fields = {
        'from': True,
        'assign': True,
        'agm': True,
        'date_signed': True,
        'customer_name': True,
        'customer_address': True,
        'customer_email': True,
        'phone_number': True,
        'notes': True
    }
    system_fields = {
        'kw': True,
        'panel': True,
        'panel_pcs': True,
        'inverter': True,
        'inverter_pcs': True,
        'roof_type': True,
        'storey': True,
        'installation_notes': False,
        'electric_power': True,
        'extra_amount': False,
        'total_price': True,
        'deposit_amount': True,
        'last_amount': True
    }
    upload_fields = {
        'upload': True
    }
    required_fields = {
        'customer_fields': customer_fields,
        'system_fields': system_fields,
        'upload_fields': upload_fields
    }
    context = {
        'current_tab': 'customer-tab',
        'leads': Lead.objects.all(),
        'sales_people': get_user_model().objects.filter(profile__title='salesman'),
        'roof_types': RoofType.objects.all(),
        'storeys': Storey.objects.all(),
        'electric_powers': ElectricPower.objects.all(),
        'customer': customer,
        'requirement': Requirement.objects.filter(customer_id=customer.id).first(),
        'credit_card': CreditCard.objects.filter(customer_id=customer.id).first(),
        'files': File.objects.filter(customer_id=customer.id),
        'power_meter_connection_disable': True,
        'required_fields': required_fields,
        'options': {
            'user_created_enabled': True,
            'customer_data_enabled': True,
            'requirement_data_enabled': True,
            'service_data_enabled': False,
            'follow_up': True,
            'file_upload_enabled': True,
            'file_list_enabled': True,
            'installation_data_enabled': False,
            'customer_check_enabled': False,
            'deposit_info_enabled': False,
            'installer_payment_data_enabled': False,
            'supplier_list_enabled': False,
            'buttons': [
                {
                    'btn_promote_name': 'btn_already_signed',
                    'btn_promote_text': 'Already Signed'
                }
            ]
        }
    }

    # Return customer form for CREATED status
    return render(request, 'customer/customer-full-form.html', context=context)


@login_required
@permission_required(['customer.deposit_list'])
def deposit_list(request):
    """Returns List of customers in DEPOSIT"""
    if request.method == 'GET':
        # Get all requirements in DEPOSIT status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                status="DEPOSIT").distinct()
        else:
            requirements = Requirement.objects.filter(Q(customer__sales_person=request.user) | Q(
                installer=request.user), status="DEPOSIT").distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Data signed': 'customer.date_signed',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Deposit': 'deposit_paid',
            'Finance': 'finance',
            'Customer Check': 'customer.customer_check',
            'Install notes': 'installation_notes',
        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'deposit-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'deposit_search_field_visible': True,
            'current_tab': 'deposit-tab'
        }

        # Return requirement list in DEPOSIT status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.deposit_search'])
def deposit_search(request):
    """Returns List of customers in DEPOSIT"""
    if request.method == 'POST':
        # get Search Key data from search form
        search_value = request.POST.get('search_value')
        print("========================")

        # Get all requirements in DEPOSIT status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                status="DEPOSIT").distinct()
        else:
            requirements = Requirement.objects.filter(
                Q(customer__sales_person=request.user) |
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value) |
                Q(installer=request.user), status="DEPOSIT").distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Data signed': 'customer.date_signed',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Deposit': 'deposit_paid',
            'Finance': 'finance',
            'Customer Check': 'customer.customer_check',
            'Install notes': 'installation_notes',
        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'deposit-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'deposit_search_field_visible': True,
            'search_value': search_value,
            'current_tab': 'deposit-tab',
        }

        # Return requirement list in DEPOSIT status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.deposit_view'])
def deposit_view(request, pk):
    """Returns a customer form in DEPOSIT status"""
    customer = Customer.objects.get(id=pk)

    # Set context.
    # leads, sales_people, roof_types, storeys, electric_powers, payments are default options loaded in Django admin
    # requirement, credit_card, files are loaded from current customer
    # options allow to configure if a section is displayed or not:
    #   follow_up: show follow up input
    #   file_upload_enabled: show file upload form
    #   file_list_enabled: show uploaded files list
    #   installation_data_enabled: show installation data form
    #   customer_check_enabled: show customer check input
    #   deposit_info_enabled: show deposit data form
    #   installer_payment_data_enabled: show installer payment form
    #   supplier_list_enabled: show list of suppliers
    # buttons allow to configure the promotion buttons to display:
    #   btn_promote_name: this is the 'name' attribute of HTML tag
    #   btn_promote_text: this is the content that will be displayed to user
    customer_fields = {
        'from': True,
        'assign': True,
        'agm': True,
        'date_signed': True,
        'customer_name': True,
        'customer_address': True,
        'customer_email': True,
        'phone_number': True,
        'notes': True
    }
    system_fields = {
        'kw': True,
        'panel': True,
        'panel_pcs': True,
        'inverter': True,
        'inverter_pcs': True,
        'roof_type': True,
        'storey': True,
        'installation_notes': True,
        'electric_power': True,
        'extra_amount': True,
        'total_price': True,
        'deposit_amount': True,
        'last_amount': True
    }
    required_fields = {
        'customer_fields': customer_fields,
        'system_fields': system_fields
    }
    context = {
        'current_tab': 'deposit-tab',
        'leads': Lead.objects.all(),
        'sales_people': get_user_model().objects.filter(profile__title='salesman'),
        'roof_types': RoofType.objects.all(),
        'storeys': Storey.objects.all(),
        'electric_powers': ElectricPower.objects.all(),
        'customer': customer,
        'requirement': Requirement.objects.filter(customer_id=customer.id).first(),
        'credit_card': CreditCard.objects.filter(customer_id=customer.id).first(),
        'files': File.objects.filter(customer_id=customer.id),
        'payments': Payment.objects.all(),
        'power_meter_connection_disable': True,
        'required_fields': required_fields,
        'options': {
            'user_created_enabled': True,
            'customer_data_enabled': True,
            'requirement_data_enabled': True,
            'service_data_enabled': False,
            'follow_up': False,
            'file_upload_enabled': True,
            'file_list_enabled': True,
            'installation_data_enabled': False,
            'customer_check_enabled': True,
            'deposit_info_enabled': True,
            'installer_payment_data_enabled': False,
            'supplier_list_enabled': False,
            'buttons': [
                {
                    'btn_promote_name': 'btn_deposit_paid',
                    'btn_promote_text': 'Deposit Paid'
                }
            ]
        }
    }

    # Return customer form for DEPOSIT status
    return render(request, 'customer/customer-full-form.html', context=context)


@login_required
@permission_required(['customer.on_file_list'])
def on_file_list(request):
    """Returns List of customers in ON_FILE"""
    if request.method == 'GET':
        # Get all requirements in ON_FILE status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                status="ON_FILE").distinct()
        else:
            requirements = Requirement.objects.filter(Q(customer__sales_person=request.user) | Q(
                installer=request.user), status="ON_FILE").distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Data signed': 'customer.date_signed',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Deposit': 'deposit_paid',
            'Customer Check': 'customer.customer_check',
            'Con/ap': 'application',
            'Install notes': 'installation_notes',
        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'on-file-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'on_file_search_visible': True,
            'current_tab': 'on-file-tab'
        }

        # Return requirement list in ON_FILE status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.on_file_search'])
def on_file_search(request):
    """Returns List of customers in ON_FILE"""
    if request.method == 'POST':

        # get Search Key data from search form
        search_value = request.POST.get('search_value')
        print("========================")

        # Get all requirements in ON_FILE status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                status="ON_FILE").distinct()
        else:
            requirements = Requirement.objects.filter(
                Q(customer__sales_person=request.user) |
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value) |
                Q(installer=request.user), status="ON_FILE").distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Data signed': 'customer.date_signed',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Deposit': 'deposit_paid',
            'Customer Check': 'customer.customer_check',
            'Con/ap': 'application',
            'Install notes': 'installation_notes',
        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'on-file-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'on_file_search_visible': True,
            'search_value': search_value,
            'current_tab': 'on-file-tab'
        }

        # Return requirement list in ON_FILE status
        return render(request, 'customer/requirement-list.html', context=context)



@login_required
@permission_required(['customer.on_file_view'])
def on_file_view(request, pk):
    """Returns a customer form in ON_FILE status"""
    customer = Customer.objects.get(id=pk)
    requirement = Requirement.objects.filter(customer_id=customer.id).first()

    # Set context.
    # leads, sales_people, roof_types, storeys, electric_powers, payments, installers are default options loaded in Django admin
    # requirement, credit_card, files are loaded from current customer
    # options allow to configure if a section is displayed or not:
    #   follow_up: show follow up input
    #   file_upload_enabled: show file upload form
    #   file_list_enabled: show uploaded files list
    #   installation_data_enabled: show installation data form
    #   customer_check_enabled: show customer check input
    #   deposit_info_enabled: show deposit data form
    #   installer_payment_data_enabled: show installer payment form
    #   supplier_list_enabled: show list of suppliers
    # buttons allow to configure the promotion buttons to display:
    #   btn_promote_name: this is the 'name' attribute of HTML tag
    #   btn_promote_text: this is the content that will be displayed to user
    customer_fields = {
        'from': True,
        'assign': True,
        'agm': True,
        'date_signed': True,
        'customer_name': True,
        'customer_address': True,
        'customer_email': True,
        'phone_number': True,
        'notes': True
    }
    system_fields = {
        'kw': True,
        'panel': True,
        'panel_pcs': True,
        'inverter': True,
        'inverter_pcs': True,
        'roof_type': True,
        'storey': True,
        'installation_notes': True,
        'electric_power': True,
        'extra_amount': True,
        'total_price': True,
        'deposit_amount': True,
        'last_amount': True,
        'power_connection': True
    }
    installation_fields = {
        'installation_date': True,
        'installer': True
    }
    supplier_fields = {
        'supplier_name': True,
        'supplier_invoice': False,
        'supplier_amount': False,
        'supplier_date_paid': False,
        'supplier_notes': False
    }
    required_fields = {
        'customer_fields': customer_fields,
        'system_fields': system_fields,
        'installation_fields': installation_fields,
        'supplier_fields': supplier_fields
    }
    context = {
        'current_tab': 'on-file-tab',
        'leads': Lead.objects.all(),
        'sales_people': get_user_model().objects.filter(profile__title='salesman'),
        'roof_types': RoofType.objects.all(),
        'storeys': Storey.objects.all(),
        'electric_powers': ElectricPower.objects.all(),
        'installers': get_user_model().objects.filter(profile__title='installer'),
        'customer': customer,
        'requirement': requirement,
        'credit_card': CreditCard.objects.filter(customer_id=customer.id).first(),
        'files': File.objects.filter(customer_id=customer.id),
        'payments': Payment.objects.all(),
        'suppliers': Supplier.objects.filter(requirement_id=requirement.id),
        'required_fields': required_fields,
        'options': {
            'user_created_enabled': True,
            'customer_data_enabled': True,
            'requirement_data_enabled': True,
            'service_data_enabled': False,
            'follow_up': False,
            'file_upload_enabled': True,
            'file_list_enabled': True,
            'installation_data_enabled': True,
            'customer_check_enabled': True,
            'deposit_info_enabled': True,
            'installer_payment_data_enabled': False,
            'supplier_list_enabled': True,
            'buttons': [
                {
                    'btn_promote_name': 'btn_confirm_all',
                    'btn_promote_text': 'Confirm All'
                },
                {
                    'btn_promote_name': 'btn_payment_order',
                    'btn_promote_text': 'Payment Order'
                }
            ]
        }
    }

    # Return customer form for ON_FILE status
    return render(request, 'customer/customer-full-form.html', context=context)


@login_required
@permission_required(['customer.order_list'])
def order_list(request):
    """Returns List of customers in ORDER"""
    if request.method == 'GET':
        # Get all requirements in ORDER status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                status="ORDER").distinct()
        else:
            requirements = Requirement.objects.filter(Q(customer__sales_person=request.user) | Q(
                installer=request.user), status="ORDER").distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Installation Date': 'installation_date',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Customer Check': 'customer.customer_check',
            'Con/ap': 'application',
            'Install notes': 'installation_notes',


        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'order-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'order_search_field_visibie': True,
            'current_tab': 'order-tab'
        }

        # Return requirement list in ORDER status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.order_search'])
def order_search(request):
    """Returns List of customers in ORDER"""
    if request.method == 'POST':
        # get Search Key data from search form
        search_value = request.POST.get('search_value')
        print("========================")

        # Get all requirements in ORDER status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                status="ORDER").distinct()
        else:
            requirements = Requirement.objects.filter(
                Q(customer__sales_person=request.user) |
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value) |
                Q(installer=request.user), status="ORDER").distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Installation Date': 'installation_date',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Customer Check': 'customer.customer_check',
            'Con/ap': 'application',
            'Install notes': 'installation_notes',


        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'order-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'order_search_field_visibie': True,
            'search_value': search_value,
            'current_tab': 'order-tab'
        }

        # Return requirement list in ORDER status
        return render(request, 'customer/requirement-list.html', context=context)



@login_required
@permission_required(['customer.order_view'])
def order_view(request, pk):
    """Returns a customer form in ORDER status"""
    customer = Customer.objects.get(id=pk)
    requirement = Requirement.objects.filter(customer_id=customer.id).first()

    # Set context.
    # leads, sales_people, roof_types, storeys, electric_powers, payments, installers are default options loaded in Django admin
    # requirement, credit_card, files are loaded from current customer
    # suppliers is loaded from current requirement
    # options allow to configure if a section is displayed or not:
    #   follow_up: show follow up input
    #   file_upload_enabled: show file upload form
    #   file_list_enabled: show uploaded files list
    #   installation_data_enabled: show installation data form
    #   customer_check_enabled: show customer check input
    #   deposit_info_enabled: show deposit data form
    #   installer_payment_data_enabled: show installer payment form
    #   supplier_list_enabled: show list of suppliers
    # buttons allow to configure the promotion buttons to display:
    #   btn_promote_name: this is the 'name' attribute of HTML tag
    #   btn_promote_text: this is the content that will be displayed to user
    customer_fields = {
        'from': True,
        'assign': True,
        'agm': True,
        'date_signed': True,
        'customer_name': True,
        'customer_address': True,
        'customer_email': True,
        'phone_number': True,
        'notes': True
    }
    system_fields = {
        'kw': True,
        'panel': True,
        'panel_pcs': True,
        'inverter': True,
        'inverter_pcs': True,
        'roof_type': True,
        'storey': True,
        'installation_notes': True,
        'electric_power': True,
        'extra_amount': True,
        'total_price': True,
        'deposit_amount': True,
        'last_amount': True,
        'power_connection': True
    }
    installation_fields = {
        'installation_date': True,
        'installer': True
    }
    supplier_fields = {
        'supplier_name': True,
        'supplier_invoice': True,
        'supplier_amount': True,
        'supplier_date_paid': False,
        'supplier_notes': False
    }
    required_fields = {
        'customer_fields': customer_fields,
        'system_fields': system_fields,
        'installation_fields': installation_fields,
        'supplier_fields': supplier_fields
    }
    context = {
        'current_tab': 'order-tab',
        'leads': Lead.objects.all(),
        'sales_people': get_user_model().objects.filter(profile__title='salesman'),
        'roof_types': RoofType.objects.all(),
        'storeys': Storey.objects.all(),
        'electric_powers': ElectricPower.objects.all(),
        'installers': get_user_model().objects.filter(profile__title='installer'),
        'customer': customer,
        'requirement': requirement,
        'credit_card': CreditCard.objects.filter(customer_id=customer.id).first(),
        'files': File.objects.filter(customer_id=customer.id),
        'suppliers': Supplier.objects.filter(requirement_id=requirement.id),
        'payments': Payment.objects.all(),
        'options': {
            'user_created_enabled': True,
            'customer_data_enabled': True,
            'requirement_data_enabled': True,
            'service_data_enabled': False,
            'follow_up': False,
            'file_upload_enabled': True,
            'file_list_enabled': True,
            'installation_data_enabled': True,
            'customer_check_enabled': True,
            'deposit_info_enabled': True,
            'installer_payment_data_enabled': True,
            'supplier_list_enabled': True,
            'required_fields': required_fields,
            'buttons': [
                {
                    'btn_promote_name': 'btn_order_paid',
                    'btn_promote_text': 'Order Paid'
                }
            ]
        }
    }

    # Return customer form for ORDER status
    return render(request, 'customer/customer-full-form.html', context=context)


@login_required
@permission_required(['customer.installation_list'])
def installation_list(request):
    """Returns List of customers in ORDER and INSTALLATION"""
    if request.method == 'GET':
        # Get all requirements in ORDER and INSTALLATION status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(status="ORDER") | Q(status="INSTALLATION")).distinct()
        else:
            requirements = Requirement.objects.filter((Q(customer__sales_person=request.user) | Q(
                installer=request.user)) & (Q(status="ORDER") | Q(status="INSTALLATION"))).distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Installation Date': 'installation_date',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',

            'Customer Check': 'customer.customer_check',
            'Con/ap': 'application',

            'Install notes': 'installation_notes',

        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'installation-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'installation_search_field_visible': True,
            'current_tab': 'installation-tab'
        }

        # Return requirement list in ORDER and INSTALLATION status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.installation_search'])
def installation_search(request):
    """Returns List of customers in ORDER and INSTALLATION"""
    if request.method == 'POST':

        # get Search Key data from search form
        search_value = request.POST.get('search_value')
        print("========================")

        # Get all requirements in ORDER and INSTALLATION status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                Q(status="ORDER") | Q(status="INSTALLATION")).distinct()
        else:
            requirements = Requirement.objects.filter(
                (Q(customer__sales_person=request.user) | 
                Q(customer__sales_person=request.user) |
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value) | 
                Q(installer=request.user)) & (Q(status="ORDER") | Q(status="INSTALLATION"))).distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Installation Date': 'installation_date',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',

            'Customer Check': 'customer.customer_check',
            'Con/ap': 'application',

            'Install notes': 'installation_notes',

        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        context = {
            'requirements': requirements,
            'url_view': 'installation-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'installation_search_field_visible': True,
            'search_value': search_value,
            'current_tab': 'installation-tab'
        }

        # Return requirement list in ORDER and INSTALLATION status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.installation_view'])
def installation_view(request, pk):
    """Returns a customer form in ORDER and INSTALLATION status"""
    customer = Customer.objects.get(id=pk)
    requirement = Requirement.objects.filter(customer_id=customer.id).first()

    # Set context.
    # leads, sales_people, roof_types, storeys, electric_powers, payments, installers are default options loaded in Django admin
    # requirement, credit_card, files are loaded from current customer
    # suppliers is loaded from current requirement
    # options allow to configure if a section is displayed or not:
    #   follow_up: show follow up input
    #   file_upload_enabled: show file upload form
    #   file_list_enabled: show uploaded files list
    #   installation_data_enabled: show installation data form
    #   customer_check_enabled: show customer check input
    #   deposit_info_enabled: show deposit data form
    #   installer_payment_data_enabled: show installer payment form
    #   supplier_list_enabled: show list of suppliers
    # buttons allow to configure the promotion buttons to display:
    #   btn_promote_name: this is the 'name' attribute of HTML tag
    #   btn_promote_text: this is the content that will be displayed to user
    customer_fields = {
        'from': True,
        'assign': True,
        'agm': True,
        'date_signed': True,
        'customer_name': True,
        'customer_address': True,
        'customer_email': True,
        'phone_number': True,
        'notes': True
    }
    system_fields = {
        'kw': True,
        'panel': True,
        'panel_pcs': True,
        'inverter': True,
        'inverter_pcs': True,
        'roof_type': True,
        'storey': True,
        'installation_notes': True,
        'electric_power': True,
        'extra_amount': True,
        'total_price': True,
        'deposit_amount': True,
        'last_amount': True,
        'power_connection': True
    }
    installation_fields = {
        'installation_date': True,
        'installer': True,
        'installer_notes': True
    }
    supplier_fields = {
        'supplier_name': True,
        'supplier_invoice': False,
        'supplier_amount': False,
        'supplier_date_paid': False,
        'supplier_notes': False
    }
    required_fields = {
        'customer_fields': customer_fields,
        'system_fields': system_fields,
        'installation_fields': installation_fields,
        'supplier_fields': supplier_fields
    }
    context = {
        'current_tab': 'installation-tab',
        'leads': Lead.objects.all(),
        'sales_people': get_user_model().objects.filter(profile__title='salesman'),
        'roof_types': RoofType.objects.all(),
        'storeys': Storey.objects.all(),
        'electric_powers': ElectricPower.objects.all(),
        'installers': get_user_model().objects.filter(profile__title='installer'),
        'customer': customer,
        'requirement': Requirement.objects.filter(customer_id=customer.id).first(),
        'credit_card': CreditCard.objects.filter(customer_id=customer.id).first(),
        'files': File.objects.filter(customer_id=customer.id),
        'suppliers': Supplier.objects.filter(requirement_id=requirement.id),
        'payments': Payment.objects.all(),
        'required_fields': required_fields,
        'options': {
            'user_created_enabled': True,
            'customer_data_enabled': True,
            'requirement_data_enabled': True,
            'service_data_enabled': False,
            'follow_up': False,
            'file_upload_enabled': True,
            'file_list_enabled': True,
            'installation_data_enabled': True,
            'customer_check_enabled': True,
            'deposit_info_enabled': True,
            'installer_payment_data_enabled': True,
            'supplier_list_enabled': True,
            'buttons': [
                {
                    'btn_promote_name': 'btn_finish_installation',
                    'btn_promote_text': 'Finish Installation'
                }
            ]
        }
    }

    # Return customer form for ORDER and INSTALLATION status
    return render(request, 'customer/customer-full-form.html', context=context)


@login_required
@permission_required(['customer.account_list'])
def account_list(request):
    """Returns List of customers in ORDER, INSTALLATION and ACCOUNT"""
    if request.method == 'GET':
        # Get all requirements in ORDER, INSTALLATION and ACCOUNT status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(Q(status="ORDER") | Q(
                status="INSTALLATION") | Q(status="ACCOUNT")).distinct()
        else:
            requirements = Requirement.objects.filter((Q(customer__sales_person=request.user) | Q(
                installer=request.user)) & (Q(status="ORDER") | Q(status="INSTALLATION") | Q(
                    status="ACCOUNT"))).distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {

            'Installation Date': 'installation_date',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'STC/ap':'stc_application',
            'Last amount': 'last_amount_balance_due',
            'STC': 'balance_due',
            'Installer':'installer_amount',
            'Payment notes':'last_amount_notes'

        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        #   summary_enabled: show summary charts at the top of the view
        #   summary: Contains all aggregated results from models
        context = {
            'requirements': requirements,
            'url_view': 'account-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'current_tab': 'account-tab',
            'summary_enabled': True,
            'account_search_field_visible': True,
            'summary': {
                'total_bank': AppData.objects.get(name='total_bank').value if AppData.objects.filter(
                    name='total_bank').exists() else 0,
                **requirements.aggregate(total_stc=Sum('stc_amount'), total_last_amount=Sum('last_amount'),
                                         total_installers=Sum('installer_amount')),
                'total_suppliers': sum(filter(None, [
                    req.supplier_set.aggregate(total_suppliers=Sum('supplier_amount')).get('total_suppliers') for req in
                    requirements]))
            }
        }

        # Return requirement list in ORDER, INSTALLATION and ACCOUNT status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.account_search'])
def account_search(request):
    """Returns List of customers in ORDER, INSTALLATION and ACCOUNT"""
    if request.method == 'POST':
        # get Search Key data from search form
        search_value = request.POST.get('search_value')
        print("========================")

        # Get all requirements in ORDER, INSTALLATION and ACCOUNT status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                Q(status="ORDER") | Q(
                status="INSTALLATION") | Q(status="ACCOUNT")).distinct()
        else:
            requirements = Requirement.objects.filter(
                Q(customer__sales_person=request.user) |
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value),
                (Q(customer__sales_person=request.user) | Q(
                installer=request.user)) & (Q(status="ORDER") | Q(status="INSTALLATION") | Q(
                    status="ACCOUNT"))).distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {

            'Installation Date': 'installation_date',
            'AGM': 'customer.agm',
            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'STC/ap':'stc_application',
            'Last amount': 'last_amount_balance_due',
            'STC': 'balance_due',
            'Installer':'installer_amount',
            'Payment notes':'last_amount_notes'

        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        #   summary_enabled: show summary charts at the top of the view
        #   summary: Contains all aggregated results from models
        context = {
            'requirements': requirements,
            'url_view': 'account-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'current_tab': 'account-tab',
            'summary_enabled': True,
            'account_search_field_visible': True,
            'search_value': search_value,
            'summary': {
                'total_bank': AppData.objects.get(name='total_bank').value if AppData.objects.filter(
                    name='total_bank').exists() else 0,
                **requirements.aggregate(total_stc=Sum('stc_amount'), total_last_amount=Sum('last_amount'),
                                         total_installers=Sum('installer_amount')),
                'total_suppliers': sum(filter(None, [
                    req.supplier_set.aggregate(total_suppliers=Sum('supplier_amount')).get('total_suppliers') for req in
                    requirements]))
            }
        }

        # Return requirement list in ORDER, INSTALLATION and ACCOUNT status
        return render(request, 'customer/requirement-list.html', context=context)



@login_required
@permission_required(['customer.account_view'])
def account_view(request, pk):
    """Returns a customer form in ORDER, INSTALLATION and ACCOUNT status"""
    customer = Customer.objects.get(id=pk)
    requirement = Requirement.objects.filter(customer_id=customer.id).first()

    # Set context.
    # leads, sales_people, roof_types, storeys, electric_powers, payments, installers are default options loaded in Django admin
    # requirement, credit_card, files are loaded from current customer
    # suppliers is loaded from current requirement
    # options allow to configure if a section is displayed or not:
    #   follow_up: show follow up input
    #   file_upload_enabled: show file upload form
    #   file_list_enabled: show uploaded files list
    #   installation_data_enabled: show installation data form
    #   customer_check_enabled: show customer check input
    #   deposit_info_enabled: show deposit data form
    #   installer_payment_data_enabled: show installer payment form
    #   supplier_list_enabled: show list of suppliers
    # buttons allow to configure the promotion buttons to display:
    #   btn_promote_name: this is the 'name' attribute of HTML tag
    #   btn_promote_text: this is the content that will be displayed to user
    customer_fields = {
        'from': True,
        'assign': True,
        'agm': True,
        'date_signed': True,
        'customer_name': True,
        'customer_address': True,
        'customer_email': True,
        'phone_number': True,
        'notes': True
    }
    system_fields = {
        'kw': True,
        'panel': True,
        'panel_pcs': True,
        'inverter': True,
        'inverter_pcs': True,
        'roof_type': True,
        'storey': True,
        'installation_notes': True,
        'electric_power': True,
        'extra_amount': True,
        'total_price': True,
        'deposit_amount': True,
        'last_amount': True,
        'power_connection': True
    }
    installation_fields = {
        'installation_date': True,
        'installer': True,
        'installer_notes': True,
        'installation_date': True,
        'installer_amount': True,
        'installer_date_paid': True
    }
    supplier_fields = {
        'supplier_name': True,
        'supplier_invoice': True,
        'supplier_amount': True,
        'supplier_date_paid': True,
        'supplier_notes': True
    }
    credit_fields = {
        'credit_card': True,
        'expires': True
    }
    deposit_fields = {
        'deposit_date_paid': True,
        'deposit_payment': True
    }
    required_fields = {
        'customer_fields': customer_fields,
        'system_fields': system_fields,
        'installation_fields': installation_fields,
        'supplier_fields': supplier_fields,
        'credit_fields': credit_fields,
        'deposit_fields': deposit_fields
    }
    context = {
        'current_tab': 'account-tab',
        'leads': Lead.objects.all(),
        'sales_people': get_user_model().objects.filter(profile__title='salesman'),
        'roof_types': RoofType.objects.all(),
        'storeys': Storey.objects.all(),
        'electric_powers': ElectricPower.objects.all(),
        'installers': get_user_model().objects.filter(profile__title='installer'),
        'customer': customer,
        'requirement': Requirement.objects.filter(customer_id=customer.id).first(),
        'credit_card': CreditCard.objects.filter(customer_id=customer.id).first(),
        'files': File.objects.filter(customer_id=customer.id),
        'suppliers': Supplier.objects.filter(requirement_id=requirement.id),
        'payments': Payment.objects.all(),
        'required_fields': required_fields,
        'options': {
            'user_created_enabled': True,
            'customer_data_enabled': True,
            'requirement_data_enabled': True,
            'service_data_enabled': False,
            'follow_up': False,
            'file_upload_enabled': True,
            'file_list_enabled': True,
            'installation_data_enabled': True,
            'customer_check_enabled': True,
            'deposit_info_enabled': True,
            'installer_payment_data_enabled': True,
            'supplier_list_enabled': True,
            'last_amount_data_enabled': True,
            'buttons': [
                {
                    'btn_promote_name': 'btn_all_paid',
                    'btn_promote_text': 'All Paid'
                }
            ]
        }
    }

    # Return customer form for ORDER, INSTALLATION and ACCOUNT status
    return render(request, 'customer/customer-full-form.html', context=context)


@login_required
@permission_required(['customer.service_list'])
def service_list(request):
    """Returns List of customers in SERVICE"""
    if request.method == 'GET':
        # Get all requirements in SERVICE status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(status="SERVICE") | Q(status="SERVICE_HOME")).distinct()
        else:
            requirements = Requirement.objects.filter(
                (Q(customer__sales_person=request.user) | Q(installer=request.user)) & (
                    Q(status="SERVICE") | Q(status="SERVICE_HOME"))).distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Installation Date': 'installation_date',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',

            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Address': 'customer.customer_address',
            'SERIVCE notes': 'service_notes'
        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        #   summary_enabled: show summary charts at the top of the view
        #   summary: Contains all aggregated results from models
        context = {
            'requirements': requirements,
            'url_view': 'service-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'service_search_field_visible': True,
            'current_tab': 'service-tab',
            'summary_enabled': False
        }

        # Return requirement list in SERVICE status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.service_search'])
def service_search(request):
    """Returns List of customers in SERVICE"""
    if request.method == 'POST':

        # get Search Key data from search form
        search_value = request.POST.get('search_value')
        print("========================")

        # Get all requirements in SERVICE status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                Q(status="SERVICE") | Q(status="SERVICE_HOME")).distinct()
        else:
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                (Q(customer__sales_person=request.user) | Q(installer=request.user)) & (
                    Q(status="SERVICE") | Q(status="SERVICE_HOME"))).distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Installation Date': 'installation_date',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',

            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Address': 'customer.customer_address',
            'SERIVCE notes': 'service_notes'
        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        #   summary_enabled: show summary charts at the top of the view
        #   summary: Contains all aggregated results from models
        context = {
            'requirements': requirements,
            'url_view': 'service-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'service_search_field_visible': True,
            'search_value': search_value,
            'current_tab': 'service-tab',
            'summary_enabled': False
        }

        # Return requirement list in SERVICE status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.service_view'])
def service_view(request, pk):
    """Returns a customer form in SERVICE status"""
    customer = Customer.objects.get(id=pk)
    requirement = Requirement.objects.filter(customer_id=customer.id).first()

    # Set context.
    # leads, sales_people, roof_types, storeys, electric_powers, payments, installers are default options loaded in Django admin
    # requirement, credit_card, files are loaded from current customer
    # suppliers is loaded from current requirement
    # options allow to configure if a section is displayed or not:
    #   follow_up: show follow up input
    #   file_upload_enabled: show file upload form
    #   file_list_enabled: show uploaded files list
    #   installation_data_enabled: show installation data form
    #   customer_check_enabled: show customer check input
    #   deposit_info_enabled: show deposit data form
    #   installer_payment_data_enabled: show installer payment form
    #   supplier_list_enabled: show list of suppliers
    # buttons allow to configure the promotion buttons to display:
    #   btn_promote_name: this is the 'name' attribute of HTML tag
    #   btn_promote_text: this is the content that will be displayed to user
    if requirement.status in ['SERVICE_HOME']:
        context = {
            'current_tab': 'service-tab',
            'installers': get_user_model().objects.filter(profile__title='installer'),
            'customer': customer,
            'requirement': Requirement.objects.filter(customer_id=customer.id).first(),
            'service_notes': ServiceNote.objects.filter(requirement_id=requirement.id),
            'options': {
                'customer_data_enabled': False,
                'requirement_data_enabled': False,
                'service_data_enabled': True,
                'follow_up': False,
                'file_upload_enabled': False,
                'file_list_enabled': False,
                'installation_data_enabled': False,
                'customer_check_enabled': False,
                'deposit_info_enabled': False,
                'installer_payment_data_enabled': False,
                'supplier_list_enabled': False,
                'last_amount_data_enabled': False,
                'service_notes_enabled': False,
                'service_note_disabled': True,
                'buttons': [
                    {
                        'btn_promote_name': 'btn_delivered_home',
                        'btn_promote_text': 'Mark as delivered'
                    }
                ]
            }
        }
    elif requirement.status in ['SERVICE']:
        context = {
            'current_tab': 'service-tab',
            'leads': Lead.objects.all(),
            'sales_people': get_user_model().objects.filter(profile__title='salesman'),
            'roof_types': RoofType.objects.all(),
            'storeys': Storey.objects.all(),
            'electric_powers': ElectricPower.objects.all(),
            'installers': get_user_model().objects.filter(profile__title='installer'),
            'customer': customer,
            'requirement': Requirement.objects.filter(customer_id=customer.id).first(),
            'credit_card': CreditCard.objects.filter(customer_id=customer.id).first(),
            'files': File.objects.filter(customer_id=customer.id),
            'suppliers': Supplier.objects.filter(requirement_id=requirement.id),
            'payments': Payment.objects.all(),
            'service_notes': ServiceNote.objects.filter(requirement_id=requirement.id),
            'options': {
                'user_created_enabled': True,
                'customer_data_enabled': True,
                'requirement_data_enabled': True,
                'service_data_enabled': False,
                'follow_up': False,
                'file_upload_enabled': True,
                'file_list_enabled': True,
                'installation_data_enabled': True,
                'customer_check_enabled': True,
                'deposit_info_enabled': True,
                'installer_payment_data_enabled': True,
                'supplier_list_enabled': True,
                'last_amount_data_enabled': True,
                'service_notes_enabled': True,
                'buttons': [
                    {
                        'btn_promote_name': 'btn_delivered',
                        'btn_promote_text': 'Mark as delivered'
                    }
                ]
            }
        }

    # Return customer form for SERVICE status
    return render(request, 'customer/customer-full-form.html', context=context)


@login_required
@permission_required(['customer.finished_list'])
def finished_list(request):
    """Returns List of customers in FINISHED and SERVICE"""
    if request.method == 'GET':
        # Get all requirements in FINISHED and SERVICE status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(Q(status="FINISHED") | Q(
                status="DELIVERED") | Q(status="DELIVERED_HOME")).distinct()
        else:
            requirements = Requirement.objects.filter(Q(customer__sales_person=request.user) | Q(
                installer=request.user), Q(status="FINISHED") | Q(status="DELIVERED") | Q(
                status="DELIVERED_HOME")).distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Installation Date': 'installation_date',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',

            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Email': 'customer.customer_email',
            'Total amount': 'total_price',
            'KW': 'kw'

        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        #   summary_enabled: show summary charts at the top of the view
        #   summary: Contains all aggregated results from models
        context = {
            'requirements': requirements,
            'url_view': 'finished-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'finished_search_field_visible': True,
            'current_tab': 'finished-tab',
            'summary_enabled': False
        }

        # Return requirement list in FINISHED and SERVICE status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.finished_search'])
def finished_search(request):
    """Returns List of customers in FINISHED and SERVICE"""
    if request.method == 'POST':

        # get Search Key data from search form
        search_value = request.POST.get('search_value')
        print("========================")

        # Get all requirements in FINISHED and SERVICE status
        if request.user.has_perm('customer.customer_view_others'):
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                Q(status="FINISHED") | Q(
                status="DELIVERED") | Q(status="DELIVERED_HOME")).distinct()
        else:
            requirements = Requirement.objects.filter(
                Q(customer__customer_name=search_value) |
                Q(customer__customer_address=search_value) |
                Q(customer__customer_email=search_value) | 
                Q(customer__phone_number=search_value) | 
                Q(customer__agm=search_value), 
                Q(customer__sales_person=request.user) | Q(
                installer=request.user), Q(status="FINISHED") | Q(status="DELIVERED") | Q(
                status="DELIVERED_HOME")).distinct()

        # Set columns to display.
        # IMPORTANT: to set columns in dict "columns",
        # 'key' is the title of the column and 'value' is the field in requirement object,
        # e.g. to get the customer name, 'requirement' object has an attribute 'customer' and this has an attribute 'customer_name'
        # so to retrieve it you will use 'customer.customer_name'
        columns = {
            'Installation Date': 'installation_date',
            'Sales': 'customer.sales_person',
            'AGM': 'customer.agm',

            'Customer Name': 'customer.customer_name',
            'Phone': 'customer.phone_number',
            'Address': 'customer.customer_address',
            'Email': 'customer.customer_email',
            'Total amount': 'total_price',
            'KW': 'kw'

        }

        # Set template context
        #   requirements: Requirements data
        #   url_view: name of url to enter each customer form
        #   columns: colums definition
        #   colspan: number of columns of the table. used to display a 'No results' message when empty
        #   current_tab: name of the current tab to set active class
        #   summary_enabled: show summary charts at the top of the view
        #   summary: Contains all aggregated results from models
        context = {
            'requirements': requirements,
            'url_view': 'finished-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'finished_search_field_visible': True,
            'search_value': search_value,
            'current_tab': 'finished-tab',
            'summary_enabled': False
        }

        # Return requirement list in FINISHED and SERVICE status
        return render(request, 'customer/requirement-list.html', context=context)


@login_required
@permission_required(['customer.finished_view'])
def finished_view(request, pk):
    """Returns a customer form in FINISHED and SERVICE status"""
    customer = Customer.objects.get(id=pk)
    requirement = Requirement.objects.filter(customer_id=customer.id).first()

    # Set context.
    # leads, sales_people, roof_types, storeys, electric_powers, payments, installers are default options loaded in Django admin
    # requirement, credit_card, files are loaded from current customer
    # suppliers is loaded from current requirement
    # options allow to configure if a section is displayed or not:
    #   follow_up: show follow up input
    #   file_upload_enabled: show file upload form
    #   file_list_enabled: show uploaded files list
    #   installation_data_enabled: show installation data form
    #   customer_check_enabled: show customer check input
    #   deposit_info_enabled: show deposit data form
    #   installer_payment_data_enabled: show installer payment form
    #   supplier_list_enabled: show list of suppliers
    # buttons allow to configure the promotion buttons to display:
    #   btn_promote_name: this is the 'name' attribute of HTML tag
    #   btn_promote_text: this is the content that will be displayed to user
    if requirement.status in ['DELIVERED_HOME']:
        context = {
            'current_tab': 'finished-tab',
            'installers': get_user_model().objects.filter(profile__title='installer'),
            'customer': customer,
            'requirement': Requirement.objects.filter(customer_id=customer.id).first(),
            'service_notes': ServiceNote.objects.filter(requirement_id=requirement.id),
            'options': {
                'customer_data_enabled': False,
                'requirement_data_enabled': False,
                'service_data_enabled': True,
                'follow_up': False,
                'file_upload_enabled': False,
                'file_list_enabled': False,
                'installation_data_enabled': False,
                'customer_check_enabled': False,
                'deposit_info_enabled': False,
                'installer_payment_data_enabled': False,
                'supplier_list_enabled': False,
                'last_amount_data_enabled': False,
                'service_notes_enabled': True,
                'buttons': [
                    {
                        'btn_promote_name': 'btn_service_home',
                        'btn_promote_text': 'Service'
                    }
                ]
            }
        }
    elif requirement.status in ['FINISHED', 'DELIVERED']:
        context = {
            'current_tab': 'finished-tab',
            'leads': Lead.objects.all(),
            'sales_people': get_user_model().objects.filter(profile__title='salesman'),
            'roof_types': RoofType.objects.all(),
            'storeys': Storey.objects.all(),
            'electric_powers': ElectricPower.objects.all(),
            'installers': get_user_model().objects.filter(profile__title='installer'),
            'customer': customer,
            'requirement': Requirement.objects.filter(customer_id=customer.id).first(),
            'credit_card': CreditCard.objects.filter(customer_id=customer.id).first(),
            'files': File.objects.filter(customer_id=customer.id),
            'suppliers': Supplier.objects.filter(requirement_id=requirement.id),
            'payments': Payment.objects.all(),
            'service_notes': ServiceNote.objects.filter(requirement_id=requirement.id),
            'options': {
                'user_created_enabled': True,
                'customer_data_enabled': True,
                'requirement_data_enabled': True,
                'service_data_enabled': False,
                'follow_up': False,
                'file_upload_enabled': True,
                'file_list_enabled': True,
                'installation_data_enabled': True,
                'customer_check_enabled': True,
                'deposit_info_enabled': True,
                'installer_payment_data_enabled': True,
                'supplier_list_enabled': True,
                'last_amount_data_enabled': True,
                'service_notes_enabled': True,
                'buttons': [
                    {
                        'btn_promote_name': 'btn_service',
                        'btn_promote_text': 'Service'
                    }
                ]
            }
        }

    # Return customer form for FINISHED and SERVICE status
    return render(request, 'customer/customer-full-form.html', context=context)


@login_required
def setupScraping(request):

    if request.method == 'POST':
        # get Search Key data from search form
        setupScraping_url = request.POST.get('setupScraping_url')
        print("=========== Scraping =============")
        pagedata = requests.get("https://bookshop.org/lists/climate-science-and-sustainable-energy-solutions-a9ef7849-d86d-40ee-a2d3-fcdda97f4a12")
        cleanpagedata = bs4.BeautifulSoup(pagedata.text, 'html.parser')
        # This searches for anything that starts with ‘id=’ and ends with a string of numbers, capturing the string of numbers
        # We need to convert the BeautifulSoup output to a string in order to search with regex
        

        # IDsearch = re.compile(r'id=(\d+)')
        # threadIDs = IDsearch.findall(str(cleanpagedata))
        scrapingResult = []
        postings = cleanpagedata.find_all("div", class_="booklist-book")
        for p in postings:
            bookData = {}
            subPageUrl = 'https://bookshop.org' + p.find('a', class_='cover')['href']
            bookData['pageUrl'] = subPageUrl.replace('\n','')
            subPageData = requests.get(subPageUrl)
            cleanSubPageData = bs4.BeautifulSoup(subPageData.text, 'html.parser')
            subPageDetails = cleanSubPageData.find_all("div", class_="measure px-4 lg:px-0 py-4 lg:py-8 grid gap-4 lg:gap-12 lg:grid-cols-1-2")
            for subPage in subPageDetails:
                title = subPage.find('h1', class_='h1 leading-tight mb-2').text
                authorsObj = subPage.find_all('span', class_='comma-after-except-last')
                authors = []
                for author in authorsObj:
                    authorName = author.find('a', class_='text-secondary').text.replace('\n','')
                    authors.append(authorName)
                imageURL = subPage.find('img', class_='w-full lg:w-book-detail-image')
                imageURL = imageURL.get('src')
                isbn = imageURL.split('/')[-1]
                isbn = isbn.split('.')[0]
                bookData['title'] = title.replace('\n','')
                bookData['author'] = authors
                bookData['imageURL'] = imageURL
                bookData['isbn'] = isbn
            scrapingResult.append(bookData)
        print("=========== Scraping =============")

        columns = {
            'Title': 'title',
            'Author': 'author',
            'ISBN': 'isbn',
            'Image URL': 'imageURL',
            'Page Url': 'pageUrl',
        }

        context = {
            'requirements': scrapingResult,
            'url_view': 'finished-view',
            'columns': columns,
            'colspan': len(columns) + 2,
            'current_tab': 'home-tab',
            'summary_enabled': False,
            'scraping_value': True,
        }
        return render(request, 'customer/home.html', context=context)