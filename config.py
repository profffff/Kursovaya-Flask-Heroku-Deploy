import os

DB_NAME = 'd18idpvuarqsho'
DB_USER = 'cssuehtndgmavj'
DB_PASS = '5432'
DB_HOST = 'ec2-54-91-223-99.compute-1.amazonaws.com'

class Config(object):
    # ...
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')