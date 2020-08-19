# def write_fillable_pdf(input_pdf_path, output_pdf_path, data_dict):
#     ANNOT_KEY = '/Annots'
#     ANNOT_FIELD_KEY = '/T'
#     ANNOT_VAL_KEY = '/V'
#     ANNOT_RECT_KEY = '/Rect'
#     SUBTYPE_KEY = '/Subtype'
#     WIDGET_SUBTYPE_KEY = '/Widget'
#     template_pdf = pdfrw.PdfReader(input_pdf_path)
#     template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true'))) 
#     annotations = template_pdf.pages[0][ANNOT_KEY]
#     for annotation in annotations:
#         if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
#             if annotation[ANNOT_FIELD_KEY]:
#                 key = annotation[ANNOT_FIELD_KEY][1:-1]
#                 if key in data_dict.keys():
#                     annotation.update(
#                         pdfrw.PdfDict(V='{}'.format(data_dict[key]))
#                     )
#     pdfrw.PdfWriter().write(output_pdf_path, template_pdf)

# # @bp.route('/payment-entrypoint')
# # def payment_entrypoint():
# #     form = SaleForm()
# #     if form.validate_on_submit():
# #         activation_code = str(uuid.uuid4())
# #         sales_tax_dict = {
# #             'Alabama': 0.04,
# #             'Alaska': 0.00,
# #             'Arizona': 0.056,
# #             'Arkansas': 0.00,
# #             'California': 0.00,
# #             'Colorado': 0.00,
# #             'Connecticut': 0.01,
# #             'District of Columbia': 0.06,
# #             'Delaware': 0.00,
# #             'Florida': 0.00,
# #             'Georgia': 0.00,
# #             'Hawaii': 0.04,
# #             'Idaho': 0.00,
# #             'Illinois': 0.00,
# #             'Indiana': 0.00,
# #             'Iowa': 0.06,
# #             'Kansas': 0.00,
# #             'Kentucky': 0.06,
# #             'Louisiana': 0.00,
# #             'Maine': 0.055,
# #             'Maryland': 0.00,
# #             'Massachusetts': 0.00,
# #             'Michigan': 0.00,
# #             'Minnesota': 0.00,
# #             'Mississippi': 0.07,
# #             'Missouri': 0.00,
# #             'Nebraska': 0.00,
# #             'Nevada': 0.0685,
# #             'New Jersey': 0.00,
# #             'New Mexico': 0.05125,
# #             'New York': 0.04,
# #             'North Carolina': 0.00,
# #             'North Dakota': 0.05,
# #             'Ohio': 0.0575,
# #             'Oklahoma': 0.00,
# #             'Pennsylvania': 0.06,
# #             'Rhode Island': 0.07,
# #             'South Carolina': 0.06,
# #             'South Dakota': 0.045,
# #             'Tennessee': 0.07,
# #             'Texas': 0.0625,
# #             'Utah': 0.061,
# #             'Vermont': 0.00,
# #             'Virginia': 0.00,
# #             'Washington': 0.065,
# #             'West Virginia': 0.06,
# #             'Wisconsin': 0.00,
# #             'Wyoming': 0.00
# #             # (Source: https://blog.taxjar.com/saas-sales-tax/, https://taxfoundation.org/2020-sales-taxes/)
# #         }
# #         sales_tax = float(3000 * sales_tax_dict[form.client_state.data])
# #         total = 3000 + sales_tax
# #         data_dict = {
# #             'receipt_date': datetime.utcnow().strftime('%m/%d/%Y %H:%M'),
# #             'agent_name': f'{str(agent.first_name).upper()} {str(agent.last_name).upper()}',
# #             'agent_email': f'{agent.email}',
# #             'agent_phone': f'({str(agent.phone_number)[0:3]}) {str(agent.phone_number)[3:6]}-{str(agent.phone_number)[6:10]}',
# #             'client_name': f'{str(form.client_name.data).upper()}',
# #             'client_street_address': f'{str(form.client_street_address.data).upper()}',
# #             'client_city': f'{str(form.client_city.data).upper()}',
# #             'client_state': f'{str(form.client_state.data).upper()}',
# #             'client_zip': f'{form.client_zip.data}',
# #             'client_email': f'{form.client_email.data}',
# #             'client_phone': f'({str(form.client_phone.data)[0:3]}) {str(form.client_phone.data)[3:6]}-{str(form.client_phone.data)[6:10]}',
# #             'sales_tax': f'${sales_tax:.2f}',
# #             'total': f'${total:.2f}',
# #             'activation_code': activation_code,
# #             'client_full_address': '{}, {}, {} {}'.format(str(form.client_street_address.data).upper(), str(form.client_city.data).upper(), str(form.client_state.data).upper(), int(form.client_zip.data)),
# #             'day': datetime.utcnow().strftime('%d'),
# #             'month': datetime.utcnow().strftime('%B'),
# #             'year': datetime.utcnow().strftime('%Y'),
# #             'icyfire_signature': 'Neil A Rutherford',
# #             'icyfire_rep_legal_name': 'Neil A Rutherford',
# #             'client_signature': form.contact_name.data,
# #             'client_rep_legal_name': form.contact_name.data
# #         }
# #         write_fillable_pdf(input_pdf_path='./app/static/agreements/online_pos_docs.pdf', output_pdf_path='./app/static/agreements/{}_online.pdf'.format(form.client_name.data), data_dict=data_dict)

# #         transfer_data = TransferData(os.environ['DROPBOX_ACCESS_KEY'])
# #         file_from = './app/static/agreements/{}_online.pdf'.format(form.client_name.data)
# #         file_to = '/receipts/online_{}.pdf'.format(form.client_name.data)
# #         transfer_data.upload_file(file_from, file_to)

# #         sale = Sale(agent_id='Online')
# #         sale.team_lead = 'Online'
# #         sale.region_lead = 'Online'
# #         sale.country_lead = 'USA-00-00-00'
# #         sale.client_name = form.client_name.data
# #         sale.client_street_address = form.client_street_address.data
# #         sale.client_city = form.client_city.data
# #         sale.client_state = form.client_state.data
# #         if form.client_state.data == 'Other':
# #             sale.client_country = 'Outside the United States'
# #             sale.client_phone_country = 0
# #         else:
# #             sale.client_country = 'United States'
# #             sale.client_phone_country = 1
# #         sale.client_zip = form.client_zip.data
# #         sale.client_phone_number = form.client_phone.data
# #         sale.client_email = form.client_email.data
# #         sale.unit_price = 3000
# #         sale.quantity = 1
# #         sale.subtotal = 3000
# #         sale.sales_tax = float(sales_tax)
# #         sale.total = float(total)
# #         sale.receipt_url = 'dropbox/home/Apps/icyfire/receipts/online_{}.pdf'.format(form.client_name.data)
# #         sale.payment_reference = 'Stripe: {} UTC'.format(datetime.utcnow())

# #         domain = Domain(activation_code=activation_code)

# #         db.session.add(sale)
# #         db.session.add(domain)
# #         db.session.commit()
# #         return redirect(url_for('promo.checkout'))

# Process payment
# @bp.route('/create-payment-intent', methods=['GET', 'POST'])
# def create_payment():
#     try:
#         data = json.loads(request.data)
#         intent = stripe.PaymentIntent.create(amount=float(3000), currency='usd')
#         return jsonify({'clientSecret': intent['client_secret']})
#     except Exception as e:
#         return jsonify(error=str(e)), 403