from google.appengine.api import memcache
import os

key_months = os.environ['CURRENT_VERSION_ID'] + '/_/months/'
key_path = os.environ['CURRENT_VERSION_ID'] + '/_/paths/'

def set_months(months):
    """Sets months in map of name ("2013/11")  and count (24)."""
    memcache.set(key_months, months)

def get_months():
    return memcache.get(key_months)

def get_path(path):
    return memcache.get(key_path + path)

def set_path(path, response):
    memcache.set(key_path + path, response)

def dirty_all():
    memcache.flush_all()
