`FlaskProxy` is a simple flask-based reverse proxy

It's goals are:

 * easy to run in docker containers
 * support configuration via the environment
 * allow extensive rewrite capability
 * facilitate proxying to HTTPs sites

## Examples

## Using FlaskProxy

You must set target URL in the environment before you start the server.
In the example below, we want all queries to the proxy to be directed
to `google.com`. 

```
$ export FLASKPROXY_DEST_URL="https://www.google.com"

$ python manage.py runserver -h 0.0.0.0
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)

- or use gunicorn as below -

$ gunicorn -b 0.0.0.0:5000 --timeout 120 --workers 3 --access-logfile -  manage:app 
[2018-02-28 13:03:53 +0530] [93324] [INFO] Starting gunicorn 19.7.1
[2018-02-28 13:03:53 +0530] [93324] [INFO] Listening at: http://0.0.0.0:5000 (93324)
[2018-02-28 13:03:53 +0530] [93324] [INFO] Using worker: sync
[2018-02-28 13:03:53 +0530] [93327] [INFO] Booting worker with pid: 93327
[2018-02-28 13:03:53 +0530] [93328] [INFO] Booting worker with pid: 93328
[2018-02-28 13:03:54 +0530] [93329] [INFO] Booting worker with pid: 93329

# in a separate terminal:
$ curl -Lv 127.0.0.1:5000
* Rebuilt URL to: 127.0.0.1:5000/
*   Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to 127.0.0.1 (127.0.0.1) port 5000 (#0)
> GET / HTTP/1.1
> Host: 127.0.0.1:5000
> User-Agent: curl/7.54.0
> Accept: */*
> 
< HTTP/1.1 200 OK
< Server: gunicorn/19.7.1
< Date: Wed, 28 Feb 2018 07:35:59 GMT
< Connection: close
< Content-Type: text/html; charset=ISO-8859-1
< Content-Length: 13825
< 
[content from google.com]
```


