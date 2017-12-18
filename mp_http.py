#!/usr/bin/env python
from multiprocessing import Process, Value
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
#from optiparse import OptionParser
import pprint
import time
import signal
import random
import math
import threading
import os
import sys
#import yappi
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
 #       metrics = self.getMetrics(port)
        metrics = self.server.metrics

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

class MyHTTPServer(ThreadingMixIn, HTTPServer):
    def __init__(self, *args, **kw):
        HTTPServer.__init__(self, *args, **kw)
        self.metrics = args[2]
#        pp = pprint.PrettyPrinter(indent=4)
#        pp.pprint(self.metrics)               
 
class HttpProc(object):
    def __init__(self, port=8080, metrics=None):
        self.port = port
        self.serve = True
        self.metrics = metrics
        self.proc = None
        self.counter = Value('i',0)

        return

    def serve_forever(self,server,counter):
        try:
            while self.serve:
                server.handle_request()
                counter.value = counter.value + 1
        except (KeyboardInterrupt, SystemExit):
            keep_running = False
            print "stop"
        finally:
            sys.exit(0)
            server.shutdown()
            server.close()
                
    def run(self):
        try:
            print('Listening on localhost:%s' % self.port)
            server = MyHTTPServer(('', self.port), RequestHandler, metrics)
            server.timeout = 5
            self.proc = Process(target=self.serve_forever,args=(server,self.counter,))
            self.proc.start()
        except KeyboardInterrupt:
            pass

    def printCounter(self):
        print("port: " + str(self.port) + " count:" + str(self.counter))

    def stopServer(self):
        self.proc.terminate()
        self.serve = False

    def join(self):
        self.proc.join()

def is_running():
    global keep_running

    return keep_running


def service_shutdown(signal, frame):
    global keep_running
    keep_running = False


def genMetrics(port):
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

    procs = []
    try:
        for port in range(port_start, port_end):
            metrics = genMetrics(port)
            t = HttpProc(port=port, metrics=metrics)
            t.run()
            procs.append(t)

    except (KeyboardInterrupt, SystemExit):
        keep_running = False
        print "Thread interuppted"

    w = 0
    now = time.time()
    while is_running():
        time.sleep(1)
        w = w + 1
        if w == 5:
          break

    later = time.time()

    print(" ")
    ct = 0
    for t in procs:
        cnt = t.counter.value
        print(str(t.port) + ":" + str(cnt)),
        ct += cnt

    print(" ")
    print("Served " + str(ct) + " requests in " + str(int(later - now)) + " seconds.")

    for t in procs:
        t.stopServer()

    print("Stopping.."),
    for t in procs:
        print(t.port),
        sys.stdout.flush()
        t.join()
    print(" ")
