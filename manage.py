import os, sys
from flask import Flask, request
from flask_script import Manager, Shell
# from bs4 import BeautifulSoup
from urlparse import urlparse
import requests

app = Flask(__name__)
manager = Manager(app)

# @app.route('/')
# def root_redirect():
#     index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/static/index.html')
#     # if (os.path.exists(index_path)):
#     return redirect('/static/index.html', code=302)
#     # else:
#     #     # index file not found, return placeholder text
#     #     return '<h3>This site is under construction and will be online soon</h3>'

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


debug = os.getenv('FLASKPROXY_DEBUG', False)
src_prefix = os.getenv('FLASKPROXY_SRC_PREFIX', '/')
dest_url = os.environ['FLASKPROXY_DEST_URL']

if (src_prefix[-1] != '/'):
    src_prefix += '/'
if (dest_url[-1] != '/'):
    dest_url += '/'

if debug: print "destination url: {0}".format(dest_url)
parsed = urlparse(dest_url)
if debug: print "Parsed dest url: {0}".format(parsed)
dest_scheme = parsed[0]
dest_host = parsed[1]
dest_url_sans_path = '{0}://{1}'.format(parsed[0], dest_host)
if (dest_url_sans_path[-1] != '/'):
    dest_url_sans_path += '/'
if debug: print "dest url sans path: {0}".format(dest_url_sans_path)

dest_url_sans_http = dest_url.replace('https:', '').replace('http:', '').replace('//', '/')
# rewrite = os.getenv('FLASKPROXY_REWRITE', False)

@app.route(src_prefix)
@app.route(src_prefix + '<path:p>')
def proxy(p = ''):
    url = dest_url + p
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    proxy_headers = dict(request.headers)
    proxy_headers['Host'] = dest_host
    if 'X-Forwarded-For' not in request.headers:
        proxy_headers['X-Forwarded-For'] = user_ip
    if 'Referer' in request.headers:
        orig_referrer = request.headers['Referer']
        t_ref = orig_referrer.replace('http://','').replace('https://','').replace('https://','')
        ref_path = "/".join(t_ref.split('/')[1:])
        #proxy_headers['Referer'] = "{0}://{1}/{2}".format(dest_scheme, dest_host, ref_path)
        proxy_headers['Referer'] = "{0}{1}".format(dest_url, ref_path)

    if (debug): 
        print "\n\nrequest url: {0}, remote_ip: {1}".format(url, user_ip)
        print "original request_header:\n{0}".format(request.headers)
        print "proxy_header:\n{0}".format(proxy_headers)

    try:
        r = requests.get(url, headers=proxy_headers)
    except Exception as e:
        # return "Service Unavailable: " + str(e), 503
        pass
    if (r.status_code == 404):
        if debug: print "proxy: 404 for " + url
        url2 = dest_url_sans_path + p
        if (url2 != url):
            try:
                if debug: print "proxy: trying " + url2
                r = requests.get(url2, headers=proxy_headers)
            except Exception as e:
                pass

    # if rewrite:
    #     decoded = r.content.decode(r.encoding)
    #     map1 = (request.url_root + src_prefix).replace('//', '/').replace(':/', '://')
    #     # map2 = ('/' + request.host + src_prefix).replace('//', '/')
    #     map2 = ('/' + src_prefix).replace('//', '/')
    #     content = decoded.replace(dest_url, map1) \
    #                      .replace(dest_url_sans_http, map2)
    #     if debug:
    #         print "map: {0} => {1}".format(dest_url, map1)
    #         print "map: {0} => {1}".format(dest_url_sans_http, map2)
    #     soup = BeautifulSoup(content, "html.parser")
    # else:
    # print r.headers
    return r.content, r.status_code, {'Content-Type': r.headers['content-type']} 

# @app.route('/favicon.ico')
# def redirect_favicon():
#     return redirect('/static/favicon.ico', code=302)

@manager.command
def routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)
        methods = ','.join(rule.methods)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, rule))
        output.append(line)
    for line in sorted(output):
        print line

if __name__ == '__main__':
    manager.run()
