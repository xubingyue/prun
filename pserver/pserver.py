#!/usr/bin/env python
#coding: utf-8
#file   : helloworld.py
#author : ning
#date   : 2013-03-13 09:42:39

import os
import sys
import socket
import re
import time
import ssl
from urlparse import urlparse

socket.setdefaulttimeout(60)

import argparse
import tornado.web
import tornado.httpserver
import tornado.httpclient

ARGS = None

class HelloHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class TunnelHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT']

    @tornado.web.asynchronous
    def get(self):
        x = self.request.uri.split('//', 1)[1]
        path = '/'+x.split('/', 1)[1]
        body = '%s %s HTTP/1.0\r\n' % (self.request.method, path)
        for k , v in self.request.headers.items():
            body += '%s: %s\r\n' % (k, v)
        body += '\r\n'
        if self.request.body:
            body += self.request.body
            body += '\r\n'
        return self.connect(body)

    @tornado.web.asynchronous
    def post(self):
        return self.get()

    @tornado.web.asynchronous
    def connect(self, firstline=None):
        if self.request.method == 'CONNECT':
            host, port = self.request.uri.split(':')
        else:
            host = self.request.host
            if host.find(':') != -1:
                host, port = self.request.host.split(':')

            else:
                if self.request.protocol == 'https':
                    port = 443
                else:
                    port = 80

        client = self.request.connection.stream

        def read_from_client(data):
            upstream.write(data)

        def read_from_upstream(data):
            # print '===<<<', data
            client.write(data)

        def client_close(data=None):
            if upstream.closed():
                return
            if data:
                upstream.write(data)
            upstream.close()

        def upstream_close(data=None):
            if client.closed():
                return
            if data:
                client.write(data)
            client.close()

        def on_connect(data=None):
            print '===<<<', data
            # data is 'HTTP/1.0 200 Connection established\r\n\r\n'
            if firstline:
                print '===>>>', firstline
                upstream.write_to_fd(firstline)
            else:
                client.write(data)

            client.read_until_close(client_close, read_from_client)
            upstream.read_until_close(upstream_close, read_from_upstream)

        def start_tunnel():
            body = "%s %s:%s HTTP/1.1\r\n\r\n" % (connect_method, host, port);
            print '===>>>', body
            upstream.write_to_fd(body)
            upstream.read_until('\r\n\r\n', on_connect)

        #https://127.0.0.1:8888/CONNECTX
        m = re.match('(.*?)://(.*?):(.*?)/(.*)', ARGS.upstream)
        upstream_protocl, upstream_host, upstream_port, connect_method = m.groups()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        print 'setup tunnel to %s' % ARGS.upstream

        if upstream_protocl == 'https':
            upstream = tornado.iostream.SSLIOStream(s, ssl_options= dict( ca_certs=None, cert_reqs=ssl.CERT_NONE))
        else:
            upstream = tornado.iostream.IOStream(s)

        upstream.connect((upstream_host, int(upstream_port)), start_tunnel)

#a normal http/https proxy, only CONNECTX allowed
class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['CONNECTX']

    @tornado.web.asynchronous
    def connectx(self):
        host, port = self.request.uri.split(':')
        client = self.request.connection.stream
        print '%s %s:%s' % (self.request.method, host, port)

        def read_from_client(data):
            upstream.write(data)

        def read_from_upstream(data):
            client.write(data)

        def client_close(data=None):
            if upstream.closed():
                return
            if data:
                upstream.write(data)
            upstream.close()

        def upstream_close(data=None):
            if client.closed():
                return
            if data:
                client.write(data)
            client.close()

        def start_tunnel():
            client.read_until_close(client_close, read_from_client)
            upstream.read_until_close(upstream_close, read_from_upstream)
            client.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)
        upstream.connect((host, int(port)), start_tunnel)

def main():
    global ARGS

    parser = argparse.ArgumentParser(prog='PROG')
    parser.add_argument('-p', '--port', type=int, default='8888')
    parser.add_argument('--https', action='store_true', help="enable https?")
    parser.add_argument('--upstream',  default='', help='upstream of tunnel, http://x.com:8888 | https://x.com:8888')

    ARGS = parser.parse_args()

    if ARGS.upstream:   #as a tunnel server
        application = tornado.web.Application([
            (r"/", HelloHandler),
            (r".*", TunnelHandler),
        ])
    else:               # as a proxy server
        application = tornado.web.Application([
            (r"/", HelloHandler),
            (r".*", ProxyHandler),
        ])

    #enable https.
    if ARGS.https:
        ssl_options = {
            "certfile": "conf/www.ning.com.cert",
            "keyfile": "conf/www.ning.com.key",
        }
        http_server = tornado.httpserver.HTTPServer(application, ssl_options=ssl_options)
    else:
        http_server = tornado.httpserver.HTTPServer(application)

    http_server.listen(ARGS.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
