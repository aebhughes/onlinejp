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
                    send_from_directory,
                    flash)
from flask.ext.mail import Mail, Message
from werkzeug.contrib.fixers import ProxyFix
from werkzeug import secure_filename
import logging
from logging.handlers import RotatingFileHandler
from operator import itemgetter
import os

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

def build_blog_list():
    blog_list = []
    for id in db:
        blog_list.append(db[id])
    
    return sorted(blog_list, key=itemgetter, reverse=True) 

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].upper() in app.config['ALLOWED_EXTENSIONS']

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/test', methods=['GET','POST'])
def test():
    #app.logger.debug('A debug message...')
    #app.logger.warn('A warn message...')
    #app.logger.info('An info message...')
    if request.method == 'POST':
        file = request.files['file']
        app.logger.info('file.content_type: {}'.format(file.content_type))
        app.logger.info('file.filename:     {}'.format(file.filename))
        app.logger.info('file.headers:      {}'.format(file.headers))
        app.logger.info('file.mimetype:     {}'.format(file.mimetype))
        app.logger.info('file.name:         {}'.format(file.name))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file', filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

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
    # upload file
    file = request.files['cv']
    print dir(file)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        app.logger.debug('File upload failed')
    # send ['email_confirm']
    cm = db['email_confirm']
    body = cm['body'].format(name=request.form['name'])
    msg = Message(subject=cm['subject'],
                  recipients=[ request.form['email'] ],
                  body=body,
                  sender=cm['from'],
                  reply_to=cm['from'])
    mail.send(msg)
    # send ['email_alert'] with attachment from upload
    cm = db['email_alert']
    body = cm['body'].format(name=request.form['name'],
                             email=request.form['email'])
    msg = Message(subject=cm['subject'],
                  recipients=[ cm['to'] ],
                  body=body,
                  sender=cm['from'])
    with app.open_resource(os.path.join(app.config['UPLOAD_FOLDER'],
                                                            filename)) as cv:
        msg.attach(filename=filename,
                   content_type=file.content_type,
                   data=cv.read()
                   )
    mail.send(msg)

    return render_template('order_confirm.html', blogs=build_blog_list())

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
