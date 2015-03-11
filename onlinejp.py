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

@app.route('/buy-now')          # home.views.buy_now
def buy_now():
    return render_template('buy_now.html', blogs=build_blog_list())

@app.route('/contact')          # home.views.contact
def contact():
    return render_template('contact.html', blogs=build_blog_list())

@app.route('/payment')          # home.views.payment
def cc_payment():
    return render_template('order_confirm.html', blogs=build_blog_list()) 

@app.route('/paypal')           # home.views.paypal
def paypal_payment():
    return redirect('/')

@app.route('/paypal-accept')    # paypal_accept (view)
def paypal_accept():
    return render_template('order_confirm.html', blogs=build_blog_list())

@app.route('/paypal-cancel')    # paypal_cancel.html (static)
def paypal_cancel():
    return render_template('paypal_cancel.html', blogs=build_blog_list())
    pass

@app.route('/blog/<slug>')
def blogs(slug):
    if slug in db:
        blog = db[slug]
        return render_template('blog_page.html', blog=blog, blogs=build_blog_list())
    return render_template('no_blog_page.html', blogs=build_blog_list())

if __name__ == '__main__':
    app.run(debug=True)
