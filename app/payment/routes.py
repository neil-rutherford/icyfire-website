import stripe
import json
import os
from flask import Flask, render_template, jsonify, request, send_from_directory, url_for, redirect, abort
from dotenv import load_dotenv, find_dotenv
from app.payment import bp
from app.payment.forms import UsSaleForm
from app.models import Sale, Domain
import pdfrw
import dropbox
import uuid
import datetime
from app.main.transfer import TransferData
from app import db

def write_fillable_pdf(input_pdf_path, output_pdf_path, data_dict):
    ANNOT_KEY = '/Annots'
    ANNOT_FIELD_KEY = '/T'
    ANNOT_VAL_KEY = '/V'
    ANNOT_RECT_KEY = '/Rect'
    SUBTYPE_KEY = '/Subtype'
    WIDGET_SUBTYPE_KEY = '/Widget'
    template_pdf = pdfrw.PdfReader(input_pdf_path)
    template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true'))) 
    annotations = template_pdf.pages[0][ANNOT_KEY]
    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                if key in data_dict.keys():
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(data_dict[key]))
                    )
    pdfrw.PdfWriter().write(output_pdf_path, template_pdf)


def write_fillable_pdf2(input_pdf_path, output_pdf_path, data_dict):
    ANNOT_KEY = '/Annots'
    ANNOT_FIELD_KEY = '/T'
    ANNOT_VAL_KEY = '/V'
    ANNOT_RECT_KEY = '/Rect'
    SUBTYPE_KEY = '/Subtype'
    WIDGET_SUBTYPE_KEY = '/Widget'
    template_pdf = pdfrw.PdfReader(input_pdf_path)
    template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true'))) 
    annotations = template_pdf.pages[1][ANNOT_KEY]
    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                if key in data_dict.keys():
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(data_dict[key]))
                    )
    pdfrw.PdfWriter().write(output_pdf_path, template_pdf)


stripe_public_key = os.environ['STRIPE_PUBLIC_KEY']
stripe_secret_key = os.environ['STRIPE_SECRET_KEY']
stripe_endpoint_secret = os.environ['STRIPE_ENDPOINT_SECRET']
dropbox_key = os.environ['DROPBOX_ACCESS_KEY']

stripe.api_key = stripe_secret_key


# CHECKOUT LANDING PAGE FOR US AUDIENCES
@bp.route('/pre/us/new/checkout', methods=['GET', 'POST'])
def us_new_checkout_landing():
    form = UsSaleForm()
    if form.validate_on_submit():
        activation_code = str(uuid.uuid4())
        sales_tax_dict = {
            'Alabama': 0.04,
            'Alaska': 0.00,
            'Arizona': 0.056,
            'Arkansas': 0.00,
            'California': 0.00,
            'Colorado': 0.00,
            'Connecticut': 0.01,
            'District of Columbia': 0.06,
            'Delaware': 0.00,
            'Florida': 0.00,
            'Georgia': 0.00,
            'Hawaii': 0.04,
            'Idaho': 0.00,
            'Illinois': 0.00,
            'Indiana': 0.00,
            'Iowa': 0.06,
            'Kansas': 0.00,
            'Kentucky': 0.06,
            'Louisiana': 0.00,
            'Maine': 0.055,
            'Maryland': 0.00,
            'Massachusetts': 0.00,
            'Michigan': 0.00,
            'Minnesota': 0.00,
            'Mississippi': 0.07,
            'Missouri': 0.00,
            'Nebraska': 0.00,
            'Nevada': 0.0685,
            'New Jersey': 0.00,
            'New Mexico': 0.05125,
            'New York': 0.04,
            'North Carolina': 0.00,
            'North Dakota': 0.05,
            'Ohio': 0.0575,
            'Oklahoma': 0.00,
            'Pennsylvania': 0.06,
            'Rhode Island': 0.07,
            'South Carolina': 0.06,
            'South Dakota': 0.045,
            'Tennessee': 0.07,
            'Texas': 0.0625,
            'Utah': 0.061,
            'Vermont': 0.00,
            'Virginia': 0.00,
            'Washington': 0.065,
            'West Virginia': 0.06,
            'Wisconsin': 0.00,
            'Wyoming': 0.00
            # (Source: https://blog.taxjar.com/saas-sales-tax/, https://taxfoundation.org/2020-sales-taxes/)
        }
        sales_tax = float(1000 * sales_tax_dict[form.client_state.data])
        total = 1000 + sales_tax
        data_dict = {
            'receipt_date': datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M'),
            'agent_name': "NEIL RUTHERFORD",
            'agent_email': 'neilrutherford@icy-fire.com',
            'agent_phone': '(720) 621-6926',
            'client_name_1': f'{str(form.client_name.data).upper()}',
            'client_name_2': f'{str(form.client_name.data).upper()}',
            'client_street_address': f'{str(form.client_street_address.data).upper()}',
            'client_city': f'{str(form.client_city.data).upper()}',
            'client_state': f'{str(form.client_state.data).upper()}',
            'client_zip': f'{form.client_zip.data}',
            'client_email_1': f'{form.client_email.data}',
            'client_email_2': f'{form.client_email.data}',
            'client_phone_1': f'({str(form.client_phone.data)[0:3]}) {str(form.client_phone.data)[3:6]}-{str(form.client_phone.data)[6:10]}',
            'client_phone_2': f'({str(form.client_phone.data)[0:3]}) {str(form.client_phone.data)[3:6]}-{str(form.client_phone.data)[6:10]}',
            'sales_tax': f'${sales_tax:.2f}',
            'total': f'${total:.2f}',
            'activation_code': activation_code,
            'client_full_address': '{}, {}, {} {}'.format(str(form.client_street_address.data).upper(), str(form.client_city.data).upper(), str(form.client_state.data).upper(), int(form.client_zip.data)),
            'day': datetime.datetime.utcnow().strftime('%d'),
            'month': datetime.datetime.utcnow().strftime('%B'),
            'year': datetime.datetime.utcnow().strftime('%Y'),
            'icyfire_signature': 'Neil A Rutherford',
            'icyfire_rep_legal_name': 'NEIL A RUTHERFORD',
            'client_signature': form.contact_name.data,
            'client_rep_legal_name': str(form.contact_name.data).upper()
        }
        write_fillable_pdf(input_pdf_path='./app/static/agreements/us_sale_online.pdf', output_pdf_path='./app/static/agreements/{}_online.pdf'.format(form.client_name.data), data_dict=data_dict)
        write_fillable_pdf2(input_pdf_path='./app/static/agreements/{}_online.pdf'.format(form.client_name.data), output_pdf_path='./app/static/agreements/{}_online.pdf'.format(form.client_name.data), data_dict=data_dict)
        transfer_data = TransferData(dropbox_key)
        file_from = './app/static/agreements/{}_online.pdf'.format(form.client_name.data)
        file_to = '/receipts/{}_{}_sale_online.pdf'.format(form.client_name.data, datetime.datetime.utcnow().strftime('%Y%m%d'))
        transfer_data.upload_file(file_from, file_to)

        sale = Sale(agent_id=None)
        sale.team_lead = None
        sale.region_lead = None
        sale.country_lead = None
        sale.client_name = form.client_name.data
        sale.client_street_address = form.client_street_address.data
        sale.client_city = form.client_city.data
        sale.client_state = form.client_state.data
        sale.client_zip = form.client_zip.data
        sale.client_phone_number = form.client_phone.data
        sale.client_email = form.client_email.data
        sale.unit_price = 1000
        sale.quantity = 1
        sale.subtotal = 1000
        sale.sales_tax = float(sales_tax)
        sale.total = float(total)
        sale.receipt_url = 'dropbox/home/Apps/icyfire/receipts/{}_sale_online.pdf'.format(form.client_name.data)
        sale.payment_reference = 'Stripe: {} UTC'.format(datetime.datetime.utcnow())

        db.session.add(sale)
        db.session.commit()

        domain = Domain(activation_code=activation_code)
        domain.sale_id = sale.id
        domain.stripe_customer_id = stripe.Customer.create(description='{}'.format(sale.client_name))['id']

        db.session.add(domain)
        db.session.commit()

        listy = [
            'District of Columbia',
            'Hawaii',
            'Iowa',
            'Kentucky',
            'Maine',
            'Mississippi',
            'Nevada',
            'New Mexico',
            'New York',
            'North Dakota',
            'Ohio',
            'Pennsylvania',
            'Rhode Island',
            'South Carolina',
            'South Dakota',
            'Tennessee',
            'Texas',
            'Utah',
            'Washington',
            'West Virginia'
        ]

        if form.client_state.data in listy:
            return redirect(url_for('payment.us_checkout', state=form.client_state.data, filename='{}_{}_sale_online.pdf'.format(form.client_name.data, datetime.datetime.utcnow().strftime('%Y%m%d')), domain_id=domain.id))
        else:
            return redirect(url_for('payment.us_checkout', state='NA', filename='{}_{}_sale_online.pdf'.format(form.client_name.data, datetime.datetime.utcnow().strftime('%Y%m%d')), domain_id=domain.id))
    
    return render_template('payment/us_checkout_landing.html', form=form, title='Sign up')


# MANUAL RENEWAL PATHWAY FOR US AUDIENCES
@bp.route('/us/renew?domain=<domain_id>')
def us_renew_checkout(domain_id):
    domain = Domain.query.filter_by(id=domain_id).first()
    old_sale = Sale.query.filter_by(id=domain.sale_id).first()
   
    new_sale = Sale(agent_id=None)
    new_sale.team_lead = None
    new_sale.region_lead = None
    new_sale.country_lead = None
    new_sale.client_name = old_sale.client_name
    new_sale.client_street_address = old_sale.client_street_address
    new_sale.client_city = old_sale.client_city
    new_sale.client_state = old_sale.client_state
    new_sale.client_zip = old_sale.client_zip
    new_sale.client_phone_number = old_sale.client_phone_number
    new_sale.client_email = old_sale.client_email
    new_sale.unit_price = old_sale.unit_price
    new_sale.quantity = old_sale.quantity
    new_sale.subtotal = old_sale.subtotal
    new_sale.sales_tax = old_sale.sales_tax
    new_sale.total = old_sale.total

    db.session.add(new_sale)
    db.session.commit()

    activation_code = str(uuid.uuid4())
    domain.activation_code = activation_code
    domain.sale_id = new_sale.id
    domain.stripe_customer_id = stripe.Customer.create(description='{}'.format(new_sale.client_name))['id']
    
    db.session.add(domain)
    db.session.commit()

    data_dict = {
        'receipt_date': datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M'),
        'agent_name': "NEIL RUTHERFORD",
        'agent_email': 'neilrutherford@icy-fire.com',
        'agent_phone': '(720) 621-6926',
        'client_name_1': f'{str(new_sale.client_name).upper()}',
        'client_street_address': f'{str(new_sale.client_street_address).upper()}',
        'client_city': f'{str(new_sale.client_city).upper()}',
        'client_state': f'{str(new_sale.client_state).upper()}',
        'client_zip': f'{new_sale.client_zip}',
        'client_email_1': f'{new_sale.client_email}',
        'client_phone_1': f'({str(new_sale.client_phone)[0:3]}) {str(new_sale.client_phone)[3:6]}-{str(new_sale.client_phone)[6:10]}',
        'sales_tax': f'${new_sale.sales_tax:.2f}',
        'total': f'${new_sale.total:.2f}',
        'activation_code': activation_code,
        'client_name_2': f'{str(new_sale.client_name).upper()}',
        'client_full_address': '{}, {}, {} {}'.format(str(new_sale.client_street_address).upper(), str(new_sale.client_city).upper(), str(new_sale.client_state).upper(), int(new_sale.client_zip)),
        'client_email_2': f'{new_sale.client_email}',
        'client_phone_2': f'({str(new_sale.client_phone)[0:3]}) {str(new_sale.client_phone)[3:6]}-{str(new_sale.client_phone)[6:10]}',
        'day': datetime.datetime.utcnow().strftime('%d'),
        'month': datetime.datetime.utcnow().strftime('%B'),
        'year': datetime.datetime.utcnow().strftime('%Y'),
        'icyfire_signature': 'Neil A Rutherford',
        'icyfire_rep_legal_name': 'NEIL A RUTHERFORD',
        'client_signature': 'Digital signature - {}'.format(datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M')),
        'client_rep_legal_name': '{} representative'.format(str(new_sale.client_name).upper())
    }

    write_fillable_pdf(input_pdf_path='./app/static/agreements/us_sale_online.pdf', output_pdf_path='./app/static/agreements/{}_online.pdf'.format(new_sale.client_name), data_dict=data_dict)
    write_fillable_pdf2(input_pdf_path='./app/static/agreements/{}_online.pdf'.format(form.client_name.data), output_pdf_path='./app/static/agreements/{}_online.pdf'.format(form.client_name.data), data_dict=data_dict)
    transfer_data = TransferData(dropbox_key)
    file_from = './app/static/agreements/{}_online.pdf'.format(new_sale.client_name)
    file_to = '/receipts/{}_{}_sale_online.pdf'.format(new_sale.client_name, datetime.datetime.utcnow().strftime('%Y%m%d'))
    transfer_data.upload_file(file_from, file_to)

    return redirect(url_for('payment.us_checkout', state=new_sale.client_state, filename='{}_{}_sale_online.pdf'.format(new_sale.client_name, datetime.datetime.utcnow().strftime('%Y%m%d')), domain_id=domain.id))


# CREATES CHECKOUT AND ADDS SALES TAX, IF APPLICABLE
@bp.route('/us/checkout?sigma=<state>&filename=<filename>&domain=<domain_id>')
def us_checkout(state, filename, domain_id):
    if state is None:
        flash("ERROR: State is required.")
        return redirect(url_for('payment.us_checkout_landing'))
    domain = Domain.query.filter_by(id=domain_id).first()
    sales_tax = {
        'District of Columbia': 'txr_1HHc6VKcikwFuPuyJERL7rPo',
        'Hawaii': 'txr_1HHc6uKcikwFuPuyAaTDHwgX',
        'Iowa': 'txr_1HHc7HKcikwFuPuyN9TvaInq',
        'Kentucky': 'txr_1HHc7aKcikwFuPuy9UdrQvlc',
        'Maine': 'txr_1HHc7xKcikwFuPuyp0tgFlyi',
        'Mississippi': 'txr_1HHc8xKcikwFuPuyRICcurVS',
        'Nevada': 'txr_1HHc9OKcikwFuPuy8LoP7br7',
        'New Mexico': 'txr_1HHc9wKcikwFuPuyzv97oqPH',
        'New York': 'txr_1HHcAFKcikwFuPuy7Dr9pUMw',
        'North Dakota': 'txr_1HHcAjKcikwFuPuyhvNEfrWW',
        'Ohio': 'txr_1HHcBGKcikwFuPuyS8XlfwBP',
        'Pennsylvania': 'txr_1HHcBtKcikwFuPuy83RouEKS',
        'Rhode Island': 'txr_1HHcCGKcikwFuPuyyj3xI8ke',
        'South Carolina': 'txr_1HHcCjKcikwFuPuyFVwJKHj7',
        'South Dakota': 'txr_1HHcD9KcikwFuPuygt55PMWh',
        'Tennessee': 'txr_1HHcDXKcikwFuPuy9ZRxazpD',
        'Texas': 'txr_1HHcE0KcikwFuPuyKBI3LJMF',
        'Utah': 'txr_1HHcEMKcikwFuPuyRShe9uVR',
        'Washington': 'txr_1HHcEkKcikwFuPuyqBm0ozaK',
        'West Virginia': 'txr_1HHcF7KcikwFuPuyyWCPWIvX'
    }

    if state != 'NA':
        session = stripe.checkout.Session.create(
            customer=domain.stripe_customer_id,
            payment_method_types=['card'], 
            line_items=[{
                'price': 'prod_HzwfSRB3FjJmry', 
                'quantity': 1
            }],
            subscription_data={
                'default_tax_rates': [sales_tax[state]]
            },
            mode='subscription', 
            success_url=url_for('payment.success', filename=filename, domain_id=domain_id, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment.us_checkout', state=state, filename=filename, domain_id=domain_id, _external=True)
        )
    else:
        session = stripe.checkout.Session.create(
            customer=domain.stripe_customer_id,
            payment_method_types=['card'], 
            line_items=[{
                'price': 'price_1HPwmGKcikwFuPuyIS5bNUJV', 
                'quantity': 1
            }],
            mode='subscription', 
            success_url=url_for('payment.success', filename=filename, domain_id=domain_id, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment.us_checkout', state=state, filename=filename, domain_id=domain_id, _external=True)
        )
    return render_template(
        'payment/us_checkout.html', 
        checkout_session_id=session['id'], 
        checkout_public_key=stripe_public_key
    )


# SUCCESS PAGE
@bp.route('/success?filename=<filename>&domain=<domain_id>')
def success(filename, domain_id):
    if not os.path.exists('./app/static/agreements/{}'.format(filename)):
        dbx = dropbox.Dropbox(dropbox_key)
        with open(f"./app/static/agreements/{filename}", 'wb') as f:
            metadata, res = dbx.files_download(path='/receipts/{}'.format(filename))
            f.write(res.content)
    return send_from_directory('static/agreements', "{}".format(filename))


# UNIVERSAL PAYMENT PROCESSING
@bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    print('WEBHOOK CALLED')

    if request.content_length > 1024 * 1024:
        print('REQUEST TOO BIG')
        abort(400)
    payload = request.get_data()
    sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = stripe_endpoint_secret
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        print('INVALID PAYLOAD')
        return {}, 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print('INVALID SIGNATURE')
        return {}, 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        customer = event['data']['object']['customer']
        domain = Domain.query.filter_by(stripe_customer_id=customer).first()
        if domain.expires_on is not None:
            time_left = domain.expires_on - datetime.datetime.utcnow()
        else:
            time_left = datetime.timedelta(0)

        purchased_time = datetime.timedelta(days=365) + time_left
        
        domain.expires_on = datetime.datetime.utcnow() + purchased_time
        db.session.add(domain)
        db.session.commit()
        print("Added one year to Domain {}".format(domain.id))

    return {}