#!/usr/bin/env python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser
import time
import signal
import random
import math
import threading
import os
import sys
from urllib2 import build_opener, Request, HTTPHandler
from urllib import quote_plus
from urlparse import parse_qs, urlparse
from prometheus_client import start_http_server, CollectorRegistry, Gauge, Metric
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
_INF = float("inf")
_MINUS_INF = float("-inf")

keep_running = True

class RequestHandler(BaseHTTPRequestHandler):
#    def __init__(self, request, client_address, server):
#        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def log_message(self, format, *args):
        return

    def do_GET(self):

        request_path = self.path
        (host, port) = self.server.server_address
        output = []
        self.send_response(200)
        self.send_header(
            'Content-Type',
            str('text/plain; version=0.0.4; charset=utf-8'))
        self.end_headers()
        self.wfile.write(self.generate_latest(port))

    def getMetrics(self, port):
        metric = []
        for index in range(100):
            metric.append(
                GaugeMetricFamily(
                    "svcs_" +
                    str(index) +
                    "_" +
                    str(port) +
                    "_documents_loaded",
                    'Help text',
                    value=random.random()))

        return metric

    def floatToGoString(self, d):
        if d == _INF:
            return '+Inf'
        elif d == _MINUS_INF:
            return '-Inf'
        elif math.isnan(d):
            return 'NaN'
        else:
            return repr(float(d))

    def generate_latest(self, port):
        '''Returns the metrics from the registry in latest text format as a string.'''
        output = []
        metrics = self.getMetrics(port)
        for metric in metrics:
            output.append('# HELP {0} {1}'.format(
                metric.name, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
            output.append(
                '\n# TYPE {0} {1}\n'.format(
                    metric.name, metric.type))
            for name, labels, value in metric.samples:
                if labels:
                    labelstr = '{{{0}}}'.format(','.join(
                        ['{0}="{1}"'.format(
                            k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                            for k, v in sorted(labels.items())]))
                else:
                    labelstr = ''
                output.append(
                    '{0}{1} {2}\n'.format(
                        name,
                        labelstr,
                        self.floatToGoString(value)))
        return ''.join(output).encode('utf-8')

class HttpThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, verbose=verbose)

        self.args = args
        self.kwargs = kwargs

        self.port = args[0]
        self.serve = True
        self.counter = 0
 
        return

    def run(self):
        try:
           print('Listening on localhost:%s' % self.port)
           server = HTTPServer(('', self.port), RequestHandler)
           while self.serve:
             server.handle_request()
             self.counter = self.counter + 1
        except (KeyboardInterrupt, SystemExit):
           keep_running = False
           print "stop"
        finally:
           sys.exit(0)
           server.shutdown()
           server.close()

    def getCounter(self):
        return self.counter

    def printCounter(self):
        print("port: " + str(self.port) + " count:" + str(self.counter))

    def stopServer(self):
        self.serve = False

def default_handler(url, method, timeout, headers, data):
    '''Default handler that implements HTTP/HTTPS connections.
    Used by the push_to_gateway functions. Can be re-used by other handlers.'''
    def handle():
        request = Request(url, data=data)
        request.get_method = lambda: method
        for k, v in headers:
            request.add_header(k, v)
        resp = build_opener(HTTPHandler).open(request, timeout=timeout)
        if resp.code >= 400:
            raise IOError("error talking to pushgateway: {0} {1}".format(
                resp.code, resp.msg))

    return handle


def basic_auth_handler(url, method, timeout, headers,
                       data, username=None, password=None):
    '''Handler that implements HTTP/HTTPS connections with Basic Auth.
    Sets auth headers using supplied 'username' and 'password', if set.
    Used by the push_to_gateway functions. Can be re-used by other handlers.'''
    def handle():
        '''Handler that implements HTTP Basic Auth.
        '''
        if username is not None and password is not None:
            auth_value = '{0}:{1}'.format(username, password).encode('utf-8')
            auth_token = base64.b64encode(auth_value)
            auth_header = b'Basic ' + auth_token
            headers.append(['Authorization', auth_header])
        default_handler(url, method, timeout, headers, data)()

    return handle


def start_http(port):
    global keep_running

    counter = 0;
    try:
        print('Listening on localhost:%s' % port)
        server = HTTPServer(('', port), RequestHandler)
        while is_running():
          server.handle_request()
          counter = counter + 1

        print("port: " + str(port) + " count:" + str(counter))

    except (KeyboardInterrupt, SystemExit):
        keep_running = False
        print "stop"
    finally:
        sys.exit(0)
        server.shutdown()
        server.close()


def is_running():
    global keep_running

    return keep_running

def service_shutdown(signal,frame):
    global keep_running
    keep_running = False

signal.signal(signal.SIGINT, service_shutdown)

if __name__ == "__main__":

    port_count = 1

    if len(sys.argv) == 2:
        try:
            port_count = int(sys.argv[1])
        except Exception as e:
            print e
            sys.exit(1)

    port_start = 9301
    port_end = port_start + port_count

    threads = []
    try:
        for port in range(port_start, port_end):
                t = HttpThread(args=(port, ))
                threads.append(t)
                t.daemon=True
                t.start()
    except (KeyboardInterrupt, SystemExit):
            keep_running = False
            print "Thread interuppted"

    while is_running():
          time.sleep(1)

    ct = 0
    for t in threads:
        cnt = t.getCounter()
        print( str(t.port) + ":" + str(cnt) ),
        ct += cnt
#        t.printCounter()
    print(" ")
    print("Served " + str(cnt) + "requests.")
   
    for t in threads:
        t.stopServer()
    
    print("Stopping.."),
    for t in threads:
        print(t.port),
        sys.stdout.flush()
        t.join()
    print(" ")
