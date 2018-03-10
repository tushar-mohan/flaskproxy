`FlaskProxy` is a simple flask-based reverse proxy

It's goals are:

 * easy to run in docker containers
 * support configuration via the environment
 * allow extensive page/url rewriting capability
 * facilitate proxying to HTTPs sites


## Using FlaskProxy

The easiest way to understand `FlaskProxy` is with examples. The examples
below increase in complexity.

Suppose I want all requests to `FlaskProxy` to be satisfied by a corresponding
request to `https://nytimes.com/<path>`. So, a request to `/section`, should map
to `https://nytimes.com/section`, and so on.

```
$ export FLASKPROXY_SPEC="https://nytimes.com"
$ python manage.py runserver

$ curl -Lv http://127.0.0.1:5000/
$ curl -Lv http://127.0.0.1:5000/section
$ curl -Lv http://127.0.0.1:5000/section/politics
```

If you need an offset, say `/section` to be added to `every` request, you'd do:
```
$ export FLASKPROXY_SPEC="https://nytimes.com/section"
```
Now, an original request of `/politics` will map to `https://nytimes.com/section/politics`.

`FlaskProxy` allows routing based on a path prefix as well.

So,

```
export FLASKPROXY_SPEC="/blog=https://john-doe.github.io"
```

will cause the pattern to be applied only when the prefix `/blog` matches.
Further, it will *strip the prefix* from the target url before making a request.
So, a request to `/blog/post/212` will translate to `https://john-doe.github.io/post/212`.
Requests that do not start with `/blog` will return an error.

Similar to a path-based routing, `FlaskProxy` also allows `name-based` routing.
```
export FLASKPROXY_SPEC="blog.jdoe.org=https://john-doe.github.io"

```
Now, only requests to `blog.jdoe.org` will be mapped. 

You can also combine, name and path-based matches. 
```
export FLASKPROXY_SPEC="jdoe.org/blog=https://john-doe.github.io"
```
In the above example, only requests to `jdoe.org/blog` will be mapped.
So, `jdoe.org/blog/home` will map to `https://john-doe.github.io/home`.

The last bit of fun, is that you can specify multiple patterns, and
`FlaskProxy` will scan them in sequence for the first match. Multiple
patterns are separated using semicolons. Whitespace will be ignored.
Let's see that in action:
```
$ FLASKPROXY_SPEC="blog.perftools.org=https://tushar-mohan.github.io ;
                   /blog=https://tushar-mohan.github.io ; 
                   https://tushar-mohan.github.io/perftools"
$ export FLASKPROXY_SPEC
```

This tells `FlaskProxy` to:
 1. map requests to `blog.perftools.org` to `https://tushar-mohan.github.io`.
 2. map *any* request that begins with `/blog` to `https://tushar-mohan.github.io`, with `/blog` stripped.
 3. map all other requests, to `https://tushar-mohan.github.io/perftools`

So, 
```
blog.perftools.org/home => https://tushar-mohan.github.io/home            # rule 1
xyz.com/blog/post/212   => https://tushar-mohan.github.io/post/212        # rule 2
abc.com/hello           => https://tushar-mohan.github.io/perftools/hello # rule 3
```

### Environment Variables
`FlaskProxy` honors the following variables:

 * `FLASKPROXY_SPEC` 
 * `FLASKPROXY_DEBUG` - set to an integer greater than 0. Higher for more verbosity.

### Running with `gunicorn`
$ gunicorn -b 0.0.0.0:5000 --timeout 120 --workers 3 --access-logfile -  manage:app 
