SECRET_KEY = 'vhcGccovggJ2b+71zs0gAqu3KeWBhc8JzPy60KNrKlZq'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['DOC', 'DOCX', 'XLS', 'XLSX', 
                          'ODT', 'PAGES', 'WPD', 'WPS', 
                          'RTF', 'PDF', 'TEX', 'TXT'])

MAIL_SERVER = 'smtpout.secureserver.net'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'lynette@yourcvservices.com'
MAIL_PASSWORD = 'fr3dalex'

STRIPE_KEY = "sk_test_4QIt0oU6OhdzMyW1CbCIA8iq"  # Test
PUB_KEY = 'pk_test_uzlMf5TXNRcKBcS43cQ35cvb' 

PAYPAL_MODE = 'sandbox'
PAYPAL_ID = 'AZy_SxC0P-4oht6ZDVlbNa0pwh0jWXLkfc6u2iB4P0yZ17kn-gM15I0JVP-C'
PAYPAL_SECRET = 'EIIktxCe1MKAcKFFe30jF3Vy2-tvFu9h7Gt6fytJuN8IszpaVG6dIKQ4g7Tm'
PAYPAL_RETURN = 'http://localhost:8000/paypal-accept/'
PAYPAL_CANCEL = 'http://localhost:8000/paypal-cancel/'
