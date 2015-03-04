#!/usr/bin/python

from flask import (Flask, 
                    render_template,
                    request,
                    session,
                    url_for, 
                    redirect, 
                    Response,
                    jsonify,
                    make_response,
                    flash)
from flask.ext.mail import Mail, Message
from werkzeug.contrib.fixers import ProxyFix
from werkzeug import secure_filename
from logging.handlers import RotatingFileHandler

import stripe
import paypalrestsdk

import couchdb

couch = couchdb.Server()
couch.resource.credentials = ('aebhughes', 'CustomSoftHer0!')

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = 'vhcGccovggJ2b+71zs0gAqu3KeWBhc8JzPy60KNrKlZq'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpg', 'png', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'alex@customsoftuk.com'
MAIL_PASSWORD = 'Custom Soft Hero!'
DEFAULT_MAIL_SENDER = 'pieter@postnetsa.co.za'
mail = Mail(app)

# Logging

handler = RotatingFileHandler('onlinejp.log', maxBytes=100000,backupCount=1)
formatter = logging.Formatter(
     "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
app.logger.addHandler(handler)

@app.route('/test')
def test():
    app.logger.debug('A debug message...')
    app.logger.warn('A warn message...')
    app.logger.info('An info message...')
    return 'Test is done'

@app.route('/')                 # home.html
def index():
    pass

@app.route('/how-it-works')     # how_works.html
def how_works():
    pass

@app.route('/buy-now')          # home.views.buy_now
def buy_now():
    pass

@app.route('/contact')          # home.views.contact
def contact():
    if request.method == 'POST':
        form = forms.ContactForm(request.POST)
        if form.is_valid():
            contact = db['email_contact']

            msg = EmailMessage(
                       subject=contact['subject'],
                       body=contact['body'].format(
                                        name=form.cleaned_data['name'],
                                        email=form.cleaned_data['email'],
                                        phone=form.cleaned_data['phone'],
                                        msg=form.cleaned_data['message'],
                                        ),
                       from_email=contact['from'],
                       to=(contact['to'],),
                       bcc=(contact['bcc'],),
                       )
            msg.send()

            app.logger.info('contact email sent')

            return render_template('thankyou.html')
    else:    
        form = forms.ContactForm()
    return render_template('contact.html')

@app.route('/payment')          # home.views.payment
def cc_payment():
    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_KEY
        token = request.POST.get('stripeToken', None)
        if not token:
            message = 'No token generated'
            return render_template('order_fail.html') 
        contact = request.session['contact']
        amt = 10000
        try:
            charge = stripe.Charge.create(
                        amount=amt,
                        currency="usd",
                        card=token,
                        description=contact['email']
                        )
            if charge['paid']:
                send_emails(contact)
                contact['charge_id'] = charge['id']
                contact.save()
                request.session['contact'] = contact
                return render_template('order_confirm.html') 
            else:
                return render_template('order_fail.html') 
        except stripe.CardError, e:
            return render_template('order_fail.html')

@app.route('/paypal')           # home.views.paypal
def paypal_payment():
    if request.method == 'POST':
        amt = 10000
        desc = "CV / Resume with LinkIn profile ($100)"
        print 'request.POST={}'.format(request.POST)

        # get access token
        paypalrestsdk.configure(
                  dict(mode=settings.PAYPAL_MODE,
                       client_id=settings.PAYPAL_ID,
                       client_secret=settings.PAYPAL_SECRET))

        # create payment object
        payment = paypalrestsdk.Payment({
          "intent": "sale",
          "payer": {"payment_method": "paypal"},
          "redirect_urls": {
                  "return_url": settings.PAYPAL_RETURN,
                  "cancel_url": settings.PAYPAL_CANCEL
                            },
           "transactions": [{
               "amount": {
                     "total": amt,
                     "currency": "USD"},
               "description": desc}]})
    
        if payment.create():
            print 'Payment [{}] created.'.format(payment.id)
            request.session['payment_id'] = payment.id
            request.session['pk'] = request.POST['pk']
            for link in payment.links:
                if link.method == 'REDIRECT':
                    redirect_url = str(link.href)
                    print 'Redirect for approval: {}'.format(redirect_url)

            # redirect to PayPal
            return redirect(redirect_url, payment)
        else:
            print 'payment.create Error: {}'.format(payment.error)
            return render(request, 'error.html')

    return redirect('/')

@app.route('/paypal-accept')    # paypal_accept (view)
def paypal_accept():
    pass

@app.route('/paypal-cancel')    # paypal_cancel.html (static)
def paypal_cancel():
    pass

@app.route('/blog/<slug>')
def blogs(slug):
    pass

@app.route('/test')
def test():
    app.logger.debug('A debug message...')
    app.logger.warn('A warn message...')
    app.logger.info('An info message...')
    return 'Test is done'

if __name__ == '__main__':
    app.run(debug=True)
