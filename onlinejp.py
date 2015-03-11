#!/usr/bin/python

from flask import (Flask, 
                    render_template,
                    request,
                    session,
                    url_for, 
                    redirect, 
                    Response,
                    jsonify,
                    Markup,
                    make_response,
                    flash)
from flask.ext.mail import Mail, Message
from werkzeug.contrib.fixers import ProxyFix
from werkzeug import secure_filename
import logging
from logging.handlers import RotatingFileHandler
from operator import itemgetter

import stripe

import paypalrestsdk

import couchdb

couch = couchdb.Server()
couch.resource.credentials = ('aebhughes', 'CustomSoftHer0!')
db = couch['yourcv']

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config.from_object('settings')
mail = Mail(app)
stripe.api_key = app.config['STRIPE_KEY']


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

def build_blog_list():
    blog_list = []
    for id in db:
        blog_list.append(db[id])
    
    return sorted(blog_list, key=itemgetter, reverse=True) 

@app.route('/')                 # home.html
def index():
    return render_template('home.html', blogs=build_blog_list())

@app.route('/how-it-works')     # how_works.html
def how_works():
    return render_template('how_works.html', blogs=build_blog_list())

@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':
        cm = db['email_contact']
        body = cm['body'].format(name=request.form['name'],
                                 email=request.form['email'],
                                 phone=request.form['phone'],
                                 msg=request.form['message'])
        msg = Message(subject=cm['subject'],
                      recipients=[cm['to']],
                      body=body,
                      sender=request.form['email'],
                      reply_to=request.form['email'])
        mail.send(msg)
        return render_template('thankyou.html', blogs=build_blog_list())
    return render_template('contact.html', blogs=build_blog_list())

@app.route('/buy-now', methods=['GET','POST'])
def buy_now():
    return render_template('buy_now.html', blogs=build_blog_list(),
                            key=app.config['PUB_KEY'])

@app.route('/payment', methods=['GET','POST'])
def payment():
    customer = stripe.Customer.create(
        email='customer@example.com',
        card=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=10000,
        currency='usd',
        description='CV Payment'
    )
    return render_template('order_confirm.html', blogs=build_blog_list())


@app.route('/paypal')
def paypal_payment():
    if request.method == 'POST':
        amt = 10000
        desc = "CV / Resume with LinkIn profile ($100)"
        print 'request.POST={}'.format(request.POST)

        # get access token
        paypalrestsdk.configure(
                  dict(mode=app.config['PAYPAL_MODE'],
                       client_id=app.config['PAYPAL_ID'],
                       client_secret=app.config['PAYPAL_SECRET']))

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
            return render_template('error.html')
    return redirect(url_for('index'))

@app.route('/blog/<slug>')
def blogs(slug):
    if slug in db:
        blog = db[slug]
        return render_template('blog_page.html', blog=blog, 
                                blogs=build_blog_list())
    return render_template('no_blog_page.html', 
                            blogs=build_blog_list())

if __name__ == '__main__':
    app.run(debug=True)
