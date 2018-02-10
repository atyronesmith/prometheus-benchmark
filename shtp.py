#!/usr/bin/env python

from multiprocessing import Process, Value
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
# from optiparse import OptionParser
import pprint
import time
import signal
import random
import math
import threading
import os
import sys
import argparse
# import yappi
from urllib2 import build_opener, Request, HTTPHandler
from urllib import quote_plus
from urlparse import parse_qs, urlparse
from prometheus_client import start_http_server, CollectorRegistry, Gauge, Metric
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
_INF = float("inf")
_MINUS_INF = float("-inf")

metric_count = 100

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
        sec = int( time.time() + (random.random()*10) ) % 60
        output = ['{} {}\n'.format(a, str(sec)
            ) for a in self.server.otput]
#        output = ['{} {}\n'.format(a, floatToGoString(
#            random.random())) for a in self.server.otput]

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
        self.metrics = metrics
        self.otput = otput
        self.server = None
        return

    def run(self):
        try:
            self.server = MyHTTPServer(
                ('', self.port), RequestHandler, self.metrics, self.otput)
            self.server.timeout = 5
            while self.serve:
                self.server.handle_request()
        except (KeyboardInterrupt, SystemExit):
            keep_running = False
            print "stop"
        finally:
            sys.exit(0)
            server.shutdown()
            server.close()

    def getCounter(self):
        if self.server is None:
          return 0
        else:
          return self.server.counter

    def stopServer(self):
        self.serve = False


class HttpProc(object):
    def __init__(self, port, port_count, proc_num):
        self.port = port
        self.port_count = port_count
        self.serve = True
        self.proc = None
        self.counter = Value('i', 0)
        self.threads = []
        self.metrics = []
        self.otput = []
        self.proc_num = proc_num

        return

    def serve_forever(self, port_start, port_count, counterx, proc_num):
        self.goThreads(port_start, port_count, proc_num)
        try:
            while self.serve:
                total = 0
                for t in self.threads:
                  total += t.getCounter()
                counterx.value = total

                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            keep_running = False
            print "stop"
        finally:
            sys.exit(0)
            server.shutdown()
            server.close()

    def run(self):
        try:
            self.proc = Process(target=self.serve_forever,
                                args=(self.port, self.port_count,self.counter,self.proc_num,))
            self.proc.start()
        except KeyboardInterrupt:
            pass

    def getCounter(self):
        return self.counter.value

    def stopServer(self):
        self.proc.terminate()
        self.serve = False

    def join(self):
        self.proc.join()

    def genOutput(self,metrics):
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

    def genMetrics(self,port,proc_num):
        metric = []
        for index in range(metric_count):
            metric.append(
                GaugeMetricFamily(
                    "svcs_" +
                    str(port) +
                    "_" +
                    str(proc_num) +
                    "_" +
                    str(index) +
                    "_total",
                    'Help text',
                    value=random.random()))

        return metric

    def goThreads(self,port_start, port_count, proc_num):
        port_end = port_start + port_count

        print("Proc(" + str(proc_num) + ") Simulating " + str(port_count) + " hosts.")
        print('Listening on localhost: ' + str(port_start) + ".." + str(port_end - 1))
        try:
            for port in range(port_start, port_end):
                self.metrics = self.genMetrics(port,proc_num)
                self.otput = self.genOutput(self.metrics)
                t = HttpThread(args=(port, ), metrics=self.metrics,
                           otput=self.otput)
                self.threads.append(t)
                t.daemon = True
                t.start()

        except (KeyboardInterrupt, SystemExit):
            keep_running = False
            print "Thread interuppted"


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


signal.signal(signal.SIGINT, service_shutdown)

if __name__ == "__main__":

    total_seconds = 10000

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mproc_count", type=int, default=1,
                        help="Number of processes to create, threads will be evenly spread across processes")
    parser.add_argument("-t", "--time", type=int, default=60,
                        help="Number of seconds to run")
    parser.add_argument("-s", "--start_port", type=int,
                        default=9301, help="First port #")
    parser.add_argument("--metric_count", type=int,
                        default=metric_count, help="# of metrics per node")
    parser.add_argument("port_count", type=int, default=1,
                        help="Number of ports to create for each process")

    args = parser.parse_args()

    total_seconds = args.time

    metric_count = args.metric_count

    print("Creating " + str(args.mproc_count) + " processes with " + str(args.port_count) + " ports each...")
    print(" to simulate " + str(args.mproc_count*args.port_count) + " hosts...")
    httpProcs = []
    port_curr = args.start_port
    for p in xrange(args.mproc_count):
        httpProc = HttpProc(port_curr, args.port_count, p)
        httpProcs.append(httpProc)
        httpProc.run()

        port_curr += args.port_count

    w = 0
    last_sum = 0
    last_delta = 0
    now = time.time()
    while is_running():
        time.sleep(1)
        w = w + 1
        if w >= total_seconds:
            break

        sum = 0
        for p in httpProcs:
            sum += p.getCounter()
        delta = (sum - last_sum) * metric_count
        if delta != last_delta:
            print("Requests " + str((sum - last_sum)) + ", Metrics / second: " + str(delta))
        last_sum = sum
        last_delta = delta

    later = time.time()

    print(" ")

    for p in httpProcs:
        p.stopServer()

    print("Stopping.."),
    for p in httpProcs:
        print('.'),
        sys.stdout.flush()
        p.join()
    print(" ")
