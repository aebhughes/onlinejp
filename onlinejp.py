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
import os, datetime

import stripe

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

# Logging for production
if not app.debug:
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(stream_handler)

def build_blog_list():
    blog_list = []
    for id in db:
        if 'email' not in id:
            blog_list.append(db[id])
    return blog_list 

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].upper() in app.config['ALLOWED_EXTENSIONS']

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/test', methods=['GET','POST'])
def test():
    #app.logger.info('An info message...')
    if request.method == 'POST':
        file = request.files['file']
        app.logger.info('file.content_type: {}'.format(file.content_type))
        app.logger.info('file.filename:     {}'.format(file.filename))
        app.logger.info('file.headers:      {}'.format(file.headers))
        app.logger.info('file.mimetype:     {}'.format(file.mimetype))
        app.logger.info('file.name:         {}'.format(file.name))
        if file and allowed_file(file.filename):
            app.logger.info('file allowed')
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            app.logger.info('upload complete')
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
    try:
        customer = stripe.Customer.create(
            email=request.form['email'],
            card=request.form['stripeToken']
        )
        charge = stripe.Charge.create(
            customer=customer.id,
            amount=10000,
            currency='usd',
            receipt_email=request.form['email'],
            description='CV Payment'
        )
    except stripe.error.CardError, e:
        app.logger.warn(' Stripe Card Error:') 
        app.logger.warn(e.json_body)
        body = e.json_body
        err = body['error']
        return render_template('order_fail.html', ref=customer.id,
                                                  message=err['message'],
                                                  blogs=build_blog_list())
    except stripe.error.InvalidRequestError, e:
        app.logger.warn('Stripe API error:') 
        app.logger.warn(e.json_body)
        return render_template('error.html')
    except stripe.error.AuthenticationError, e:
        app.logger.warn('Stripe Authentication error:') 
        app.logger.warn(e.json_body)
        return render_template('error.html')
    except stripe.error.APIConnectionError, e:
        app.logger.warn('Stripe Network error:') 
        app.logger.warn(e.json_body)
        return render_template('order_retry.html')
    except stripe.error.StripeError, e:
        app.logger.warn('General Stripe error:') 
        app.logger.warn(e.json_body)
        return render_template('error.html')
    except Exception, e:
        app.logger.warn('General error:') 
        app.logger.warn(e.json_body)
        return render_template('error.html')
    
    # upload file
    file = request.files['cv']
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

    return render_template('order_confirm.html', ref=customer.id,
                            blogs=build_blog_list())

@app.route('/blog/<slug>')
def blogs(slug):
    if slug in db:
        blog = db[slug]
        return render_template('blog_page.html', blog=blog, 
                                blogs=build_blog_list())
    return render_template('no_blog_page.html', 
                            blogs=build_blog_list())

def slugify(title):
    slug = title.replace(' ','-')
    return slug.lower()

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == "POST":
        file = request.files['file']
        if file:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                fname = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(fname)
                f = open(fname, 'r').read()
                blog = {
                        '_id': slugify(request.form['title']),
                        'title': request.form['title'],
                        'date': str(datetime.date.today()),
                        'body': f
                        }
                db.save(blog)
            else:
                flash('file type not allowed')
        else:
            flash('File upload failed')
    blogs = []
    for id in db:
        if 'email' not in id:
            blogs.append(db[id])
    return render_template('admin.html', blogs=blogs)

@app.route('/delete/<doc_id>', methods=['GET','POST'])
def delete(doc_id):
    doc = db[doc_id]
    db.delete(doc)
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)
