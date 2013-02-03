#!/usr/bin/env python
#coding: utf8

import mimetools
import itertools
import urllib
import base64
from tornado.escape import xhtml_escape, json_decode
from tornado.httputil import url_concat
from tornado.auth import httpclient, OAuthMixin
from tornado.httpclient import AsyncHTTPClient
from .utils import Json

class DropboxMixin(OAuthMixin):
    """Dropbox OAuth authentication.

    Uses the app settings dropbox_consumer_key and dropbox_consumer_secret.

    Usage::
    
        class DropboxLoginHandler(RequestHandler, DropboxMixin):
            @asynchronous
            def get(self):
                if self.get_argument("oauth_token", None):
                    self.get_authenticated_user(self._on_auth)
                    return
                self.authorize_redirect()

            def _on_auth(self, user):
                if not user:
                    raise tornado.web.HTTPError(500, "Dropbox auth failed")
                # save the user using e.g. set_secure_cookie
    """
    _OAUTH_VERSION = "1.0"
    # note www vs api.dropbox.com in authorize url
    _OAUTH_REQUEST_TOKEN_URL = "https://api.dropbox.com/1/oauth/request_token"
    _OAUTH_ACCESS_TOKEN_URL = "https://api.dropbox.com/1/oauth/access_token"
    _OAUTH_AUTHORIZE_URL = "https://www.dropbox.com/1/oauth/authorize"

 
    def dropbox_request(self, subdomain, path, callback, access_token,
                        post_args=None, put_body=None, **args):
        """Fetches the given API operation.

        The request is defined by a combination of subdomain (either
        "api" or "api-content") and path (such as "/1/metadata/sandbox/").
        See the Dropbox REST API docs for details:
        https://www.dropbox.com/developers/reference/api

        For GET requests, arguments should be passed as keyword arguments
        to dropbox_request.  For POSTs, arguments should be passed
        as a dictionary in `post_args`.  For PUT, data should be passed
        as `put_body`

        Example usage::
        
            class MainHandler(tornado.web.RequestHandler,
                              async_dropbox.DropboxMixin):
                @tornado.web.authenticated
                @tornado.web.asynchronous
                def get(self):
                    self.dropbox_request(
                        "api", "/1/metadata/sandbox/"
                        access_token=self.current_user["access_token"],
                        callback=self._on_metadata)

                def _on_metadata(self, response):
                    response.rethrow()
                    metadata = json.loads(response.body)
                    self.render("main.html", metadata=metadata)
        """
        url = "https://%s.dropbox.com%s" % (subdomain, path)
        if access_token:
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            assert not (put_body and post_args)
            if put_body is not None:
                method = "PUT"
            elif post_args is not None:
                method = "POST"
            else:
                method = "GET"
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            args.update(oauth)
        if args: url += "?" + urllib.urlencode(args)
        http = AsyncHTTPClient()

        if post_args is not None:
            http.fetch(url, method=method, body=urllib.urlencode(post_args),
                       callback=callback)
        else:
            http.fetch(url, method=method, body=put_body, callback=callback)

    def _oauth_consumer_token(self):
        return self.settings['dropbox']

    def _oauth_get_user(self, access_token, callback):
        callback(dict(
                access_token=access_token,
                uid=self.get_argument('uid'),
                ))


class YoudaoMixin(OAuthMixin):
    '''
    from xcat.third import YoudaoMixin
    from tornado.web import asynchronous

    @route(r"/test")
    class Test(RequestHandler, YoudaoMixin):

        @asynchronous
        def get(self):
            if self.get_argument("oauth_token", None):
                self.get_authenticated_user(self._on_auth)
                return
            self.authorize_redirect(self.request.full_url())
          
        def _on_auth(self, user):
            print user
            self.finish()
    '''
    _BASE_URL = 'http://note.youdao.com'
    #_BASE_URL = 'http://sandbox.note.youdao.com'

    _OAUTH_REQUEST_TOKEN_URL = "%s/oauth/request_token" % _BASE_URL
    _OAUTH_ACCESS_TOKEN_URL = "%s/oauth/access_token" % _BASE_URL
    _OAUTH_AUTHORIZE_URL = "%s/oauth/authorize" % _BASE_URL
    _OAUTH_NO_CALLBACKS = False
    _OAUTH_VERSION = "1.0"

    def _to_header(self, kw):
        s = ", ".join(['%s="%s"' % (k, self._quote(v)) for k, v in kw.iteritems() if k.startswith('oauth_')])
        h = 'OAuth %s' % s
        return {'Authorization': h}

    def _quote(self, s):
        s = urllib.quote(str(s), safe="~")
        return s

    def youdao_multipart_post(self, _path, callback, access_token, **post_args):
        url   = "%s/%s" % (self._BASE_URL, _path)
        oauth = self._oauth_request_parameters(
                url, access_token, {}, method='POST')
        args = {}
        args.update(oauth)
        callback = self.async_callback(self._on_youdao_request, callback)
        http     = httpclient.AsyncHTTPClient()
        headers  = self._to_header(args)
        
        
        form = MultiPartForm()
        for k in post_args:
            form.add_field(k, post_args[k])

        headers['Content-Type'] = form.get_content_type() 
      
        http.fetch(url, method="POST", headers=headers,
                   body=str(form), callback=callback)


    def youdao_request(self, path, callback, access_token=None,
            post_args=None, **args):
        url = "%s/%s" % (self._BASE_URL, path)
        if access_token:
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            method = "POST" if post_args is not None else "GET"
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            all_args.update(oauth)
            args = all_args

        callback = self.async_callback(self._on_youdao_request, callback)
        http = httpclient.AsyncHTTPClient()
        if post_args is not None:
            http.fetch(url, method="POST",
                       body=urllib.urlencode(args), callback=callback)
        else:
            http.fetch(url_concat(url, args), callback=callback)

    def _on_youdao_request(self, callback, response):
        if response.error:
            print response.error
            print response.request.url
            print response.body
            callback(None)
            return

        callback(Json.decode(response.body))

    def _oauth_get_user(self, access_token, callback):
        callback = self.async_callback(self._parse_user_response, callback)
        self.youdao_request(
            "yws/open/user/get.json",
            access_token=access_token, callback=callback
        )

    def _parse_user_response(self, callback, user):
        callback(user)

    def _oauth_consumer_token(self):
        token = dict(
            key = self.settings['youdao']['consumer_key'],
            secret = self.settings['youdao']['consumer_secret']
        )
        return token



class MultiPartForm(object):
    """Helper class to build a multipart form
    Copied from http://www.doughellmann.com/PyMOTW/urllib2/
    """

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, body, mimetype):
        """Add a file to be uploaded."""
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        """Return a string representing the form data,
        including attached files.
        """
        # Build a list of lists, each containing "lines" of the
        # request. Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [part_boundary,
             'Content-Disposition: form-data; name="%s"' % name,
             '',
             value,
             ]
            for name, value in self.form_fields
        )

        # Add the files to upload
        parts.extend(
            [part_boundary,
             'Content-Disposition: form-data; name="%s"; filename="%s"' %\
             (field_name, filename),
             'Content-Type: %s' % content_type,
             '',
             body,
             ]
            for field_name, filename, content_type, body in self.files
        )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)