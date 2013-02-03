#!/usr/bin/env python
# coding: utf8

from xcat.web import RequestHandler, route

@route(r"/")
class Index(RequestHandler):
    '''default'''

    def get(self):
        self.write('hello word')