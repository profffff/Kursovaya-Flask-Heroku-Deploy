import os

#DB_URL = 'postgres://cssuehtndgmavj:4a96332271add397fcf4ede36bbb3fa94a77ab2329f78c4f051d2c5ac306fd58@ec2-54-91-223-99.compute-1.amazonaws.com:5432/d18idpvuarqsho'
# DB_NAME = 'd18idpvuarqsho'
# DB_USER = 'cssuehtndgmavj'
# DB_PASS = '4a96332271add397fcf4ede36bbb3fa94a77ab2329f78c4f051d2c5ac306fd58'
# DB_PORT = '5432'
# DB_HOST = 'ec2-54-91-223-99.compute-1.amazonaws.com'

DB_NAME = 'words'
DB_USER = 'admin'
DB_PASS = 'admin'
DB_HOST = 'localhost'
DB_PORT = '5432'

class Config(object):
    # ...
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')