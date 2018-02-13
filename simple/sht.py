#!/usr/bin/env python

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

METRIC_COUNT=100

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
        self.server.counter += 1

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
#        output = []
#        metrics = self.server.metrics

#        rand_value = random.random()

#        st = time.time()
#        for metric in metrics:
#            output.append('# HELP {0} {1}'.format(
#                metric.name, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
#            output.append(
#                '\n# TYPE {0} {1}\n'.format(
#                    metric.name, metric.type))
#            for name, labels, value in metric.samples:
#                if labels:
#                    labelstr = '{{{0}}}'.format(','.join(
#                        ['{0}="{1}"'.format(
#                            k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
#                            for k, v in sorted(labels.items())]))
#                else:
#                    labelstr = ''
#                output.append(
#                    '{0}{1} {2}\n'.format(
#                        name,
#                        labelstr,
#                        self.floatToGoString(rand_value)))

#        en = time.time()
#        print(str(en - st))
        output = ['{} {}\n'.format(a,floatToGoString(random.random())) for a in self.server.otput]

        return ''.join(output).encode('utf-8')

class MyHTTPServer(HTTPServer):
     def __init__(self, server_address, RequestHandlerClass, metrics, otput):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.metrics = metrics
        self.otput = otput
        self.counter = 0
 
class HttpThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None, metrics=None, otput=None):
        threading.Thread.__init__(
            self,
            group=group,
            target=target,
            name=name,
            verbose=verbose)

        self.args = args
        self.kwargs = kwargs

        self.port = args[0]
        self.serve = True
        self.counter = 0
        self.metrics = metrics
        self.otput = otput
        self.server = None
        return

    def run(self):
        try:
            self.server = MyHTTPServer(('', self.port), RequestHandler, self.metrics, self.otput)
            self.server.timeout = 5
#            yappi.start()
            while self.serve:
                self.server.handle_request()
#                self.counter = self.counter + 1
#            yappi.get_func_stats().print_all()               
        except (KeyboardInterrupt, SystemExit):
            keep_running = False
            print "stop"
        finally:
            sys.exit(0)
            server.shutdown()
            server.close()

    def getCounter(self):
        return self.server.counter

    def printCounter(self):
        print("port: " + str(self.port) + " count:" + str(self.counter))

    def stopServer(self):
        self.serve = False

def is_running():
    global keep_running

    return keep_running


def service_shutdown(signal, frame):
    global keep_running
    keep_running = False


def floatToGoString(d):
    if d == _INF:
        return '+Inf'
    elif d == _MINUS_INF:
        return '-Inf'
    elif math.isnan(d):
        return 'NaN'
    else:
        return repr(float(d))


def genOutput(metrics):
    output = []
    for metric in metrics:
        bld = []
        bld.append('# HELP {0} {1}'.format(
             metric.name, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
        bld.append(
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
            bld.append(
                '{0}{1}'.format(
                name,
                labelstr))

        output.append(''.join(bld))

    return output

def genMetrics(port):
    metric = []
    for index in range(METRIC_COUNT):
        metric.append(
           GaugeMetricFamily(
                 "svcs_" +
                 str(port) +
                 "_" +
                 str(index) +
                 "_total",
                 'Help text',
                 value=random.random()))

    return metric

def goThreads(port_start,port_count):
    threads = []

    port_end = port_start + port_count

    print("Simulating " + str(port_count) + " hosts.")
    print('Listening on localhost:'),
    try: 
      for port in range(port_start, port_end):
        metrics = genMetrics(port)
        otput = genOutput(metrics)

        print('%s' % port),

        t = HttpThread(args=(port, ), metrics=metrics, otput=otput)
        threads.append(t)
        t.daemon = True
        t.start()
    except (KeyboardInterrupt, SystemExit):
        keep_running = False
        print "Thread interuppted"

    return threads


signal.signal(signal.SIGINT, service_shutdown)

if __name__ == "__main__":

    port_count = 1
    total_polls = 10000

    if len(sys.argv) >= 2:
        try:
            port_count = int(sys.argv[1])
        except Exception as e:
            print e
            sys.exit(1)

    if len(sys.argv) >= 3:
        try:
            total_polls = int(sys.argv[2])
        except Exception as e:
            print e
            sys.exit(1)

    port_start = 9301
    port_end = port_start + port_count

    threads = []
    try:
        print("Simulating " + str(port_count) + " hosts.")
        print('Listening on localhost:'),
        for port in range(port_start, port_end):
            metrics = genMetrics(port)
            otput = genOutput(metrics)

            print('%s' % port),

            t = HttpThread(args=(port, ), metrics=metrics, otput=otput)
            threads.append(t)
            t.daemon = True
            t.start()
    except (KeyboardInterrupt, SystemExit):
        keep_running = False
        print "Thread interuppted"

    print("")
    w = 0
    last_sum = 0
    last_delta = 0
    now = time.time()
    while is_running():
        time.sleep(1)
        w = w + 1
        if w >= total_polls:
          break

        sum = 0
        for t in threads:
            sum += t.getCounter()
        delta = (sum - last_sum) * METRIC_COUNT
        if delta != last_delta:
          print("Metrics / second: " + str( delta ))
        last_sum = sum
        last_delta = delta

    later = time.time()

    print(" ")
    ct = 0
    for t in threads:
        cnt = t.counter
        print(str(t.port) + ":" + str(cnt)),
        sys.stdout.flush()
        ct += cnt
#        t.printCounter()
    print(" ")
    print("Served " + str(ct) + " requests in " + str(int(later - now)) + " seconds.")

    for t in threads:
        t.stopServer()

    print("Stopping.."),
    for t in threads:
        print('.'),
        sys.stdout.flush()
        t.join()
    print(" ")
