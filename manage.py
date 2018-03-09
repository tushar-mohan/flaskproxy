import os, sys
from flask import Flask, request
from flask_script import Manager, Shell
# from bs4 import BeautifulSoup
from urlparse import urlparse
import requests

app = Flask(__name__)
manager = Manager(app)
debug = os.getenv('FLASKPROXY_DEBUG', False)
debug_headers = os.getenv('FLASKPROXY_DEBUG_HEADERS', False)



# this function will read the environment variable FLASKPROXY_SPEC
# It will expect a string of the format:
# [matchhost1][/matchprefix1]=[targeturl1];[matchhost2][/matchprefix2]=[targeturl2]...
# 
# 1. Whitespace will be ignored. 
# 2. Match fields are both optional. A missing match host is equivalent to the wildcard host (*).
#    A missing match prefix is equivalent to /.
# 3. Target urls are required.
# 4. Separate multiple such <match>=<target> patterns using semicolon (;)
#
# e.g.,
# FLASKPROXY_SPEC="blog.perftools.org=https://tushar-mohan.github.io ; 
#                  perftools.org/blog=https://tushar-mohan.github.io ;
#                       perftools.org=https://tushar-mohan.github.io/perftools;
#                                     https://google.com"
#
# The function will return a list (order matters!), like:
# [ 
#    { 
#              'matchHost': 'blog.perftools.org',
#            'matchPrefix': '/',
#             'targetHost': 'https://tushar-mohan.github.io',
#           'targetPrefix': '/'
#    },
#    { 
#              'matchHost': 'perftools.org',
#            'matchPrefix': '/blog',
#             'targetHost': 'https://tushar-mohan.github.io',
#           'targetPrefix': '/'
#    },
#    { 
#              'matchHost': 'perftools.org',
#            'matchPrefix': '/',
#             'targetHost': 'https://tushar-mohan.github.io',
#           'targetPrefix': '/perftools'
#    },
#    { 
#              'matchHost': '*',
#            'matchPrefix': '/',
#             'targetHost': 'https://google.com',
#           'targetPrefix': '/'
#    }
# ]
       
def create_spec_list():
    spec = os.environ.get('FLASKPROXY_SPEC')
    if not spec:
        print sys.stderr, "FLASKPROXY_SPEC must be set in the environment"
        sys.exit(1)
    if (debug):
        print "FLASKPROXY_SPEC={0}".format(spec)
    spec = spec.replace(' ','').replace('\n',';').replace('\t','')
    retlist = []
    # split on semicolon and remove empty patterns
    patterns =  [ x for x in spec.split(';') if x ]
    for p in patterns:
        scheme = 'https' if 'https' in p else 'http'

        # remove http/https from target so it's easier to pick out
        # the host/prefix part from the target
        p = p.replace('https://','').replace('http://','')

        if not '=' in p:
            target = p
            match = ''
        else:
            (match, target) = p.split('=')

        # match processing
        (mh, mp) = ('*', '/')
        if '/' in match:
            (mh, mp) = match.split('/', 1)
            mp = '/' + mp
        else:
            (mh, mp) = (match, '/')
        mh = mh or '*'
        mp = mp or '/'

        # target processng
        if '/' in target:
            (th, tp) = target.split('/',1)
            tp = '/' + tp
        else:
            (th, tp) = (target, '/')
        tp = tp or '/'
       
        r = {'matchHost': mh, 'matchPrefix': mp, 'targetHost': scheme + '://' +th, 'targetPrefix': tp}
        retlist.append(r)

    if (debug):
        print 'spec table:\n{0}'.format(retlist)
    return retlist


spec_list = create_spec_list()


def get_match(host, prefix):
    for p in spec_list:
        if ((host == p['matchHost']) or (p['matchHost'] == '*')):
            if (prefix.startswith(p['matchPrefix'])):
                return p
    return {}


@app.route('/_version')
def version():
    try:
        f = open('version', 'r')
        v =  f.read()
    except:
        v = ''
    return v

@app.route('/_healthz')
def health_check():
    return "OK\n"



# request: http://127.0.0.1:5000/alert/xyzabc/test?x=y
# 
# request.url:                 http://127.0.0.1:5000/alert/xyzabc/test?x=y
# request.base_url:            http://127.0.0.1:5000/alert/xyzabc/test
# request.url_charset:         utf-8
# request.url_root:            http://127.0.0.1:5000/
# str(request.url_rule):       /alert/xyzabc/test
# request.host_url:            http://127.0.0.1:5000/
# request.host:                127.0.0.1:5000
# request.script_root:
# request.path:                /alert/xyzabc/test
# request.full_path:           /alert/xyzabc/test?x=y
@app.route('/')
@app.route('/<path:p>')
def proxy(p = ''):
    x = get_match(request.host, request.path)
    p = request.path
    if not x:
        return "No match for {0}/{1}: ".format(request.host, request.path), 501
    dest_url = x['targetHost'] + x['targetPrefix']
    if (debug):
        print "\n----\n"
        print "match: {0}\n".format(str(x))
    if p.startswith(x['matchPrefix']):
        p = p.replace(x['matchPrefix'], '', 1)
    if not p.startswith('/'):
        p = '/' + p

    url = dest_url + p
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    proxy_headers = dict(request.headers)
    proxy_headers['Host'] = x['targetHost'].replace('https://','').replace('http://','')
    if 'X-Forwarded-For' not in request.headers:
        proxy_headers['X-Forwarded-For'] = user_ip
    if 'Referer' in request.headers:
        orig_referrer = request.headers['Referer']
        t_ref = orig_referrer.replace('http://','').replace('https://','').replace('http://','')
        ref_path = "/".join(t_ref.split('/')[1:])
        proxy_headers['Referer'] = "{0}/{1}".format(dest_url, ref_path)

    if (debug): 
        print "request url: {0}, remote_ip: {1}".format(request.url, user_ip)
        if (debug_headers):
            print "original request_header:\n{0}".format(request.headers)
            print "proxy_header:\n{0}".format(proxy_headers)
        print "proxy: attempting {0}".format(url)
    
    try:
        r = requests.get(url, headers=proxy_headers)
    except Exception as e:
        pass

    if (r.status_code == 404):
        if debug: print "proxy: 404 for " + url
        url2 = x['targetHost'] + p
        if (url2 != url):
            try:
                if debug: print "proxy: second attempt " + url2
                r = requests.get(url2, headers=proxy_headers)
            except Exception as e:
                pass
    if (r.status_code >= 400):
        print "WARN: Got {0} for {1}".format(r.status_code, request.url)
    return r.content, r.status_code, {'Content-Type': r.headers['content-type']} 


@manager.command
def routes():
    for r in spec_list:
        print "{0}{1} => {2}{3}".format(r['matchHost'], r['matchPrefix'], r['targetHost'], r['targetPrefix'])

if __name__ == '__main__':
    manager.run()
