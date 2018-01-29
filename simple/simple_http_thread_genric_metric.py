#!/usr/bin/env python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser
import random
import math
import threading
import os
import sys
from urllib2 import build_opener, Request, HTTPHandler
from urllib import quote_plus
from urlparse import parse_qs, urlparse
from prometheus_client import start_http_server,CollectorRegistry,Gauge,Metric
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
_INF = float("inf")
_MINUS_INF = float("-inf")
class RequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        
        request_path = self.path
        (host,port)= self.server.server_address
        output = []
        self.send_response(200)
        self.send_header('Content-Type', str('text/plain; version=0.0.4; charset=utf-8'))
        self.end_headers()        
        self.wfile.write(self.generate_latest(port))

    def getMetrics(self,port):
        metrics=[]
        data={"fast": random.random(),"slow": random.random()} 
        for index in range(100):
            metric = Metric("svcs_"+str(index)+"_"+ str(port)+"_documents_loaded", 'Help text', 'gauge')
            for k, v in data.items():
               metric.add_sample("svcs_"+str(index)+"_"+ str(port)+"_documents_loaded",value=v, labels={'repository': k})
            metrics.append(metric)   
            #metrics.append(GaugeMetricFamily("svcs_"+str(index)+"_"+ str(port)+"_documents_loaded", 'Help text', value=random.random()))
          
        return metrics  

    def floatToGoString(self,d):
       if d == _INF:
          return '+Inf'
       elif d == _MINUS_INF:
          return '-Inf'
       elif math.isnan(d):
          return 'NaN'
       else:
          return repr(float(d))

    def generate_latest(self,port):
        '''Returns the metrics from the registry in latest text format as a string.'''
        output = []
        metrics=self.getMetrics(port)
        for metric in metrics:
           output.append('# HELP {0} {1}'.format(
           metric.name, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
           output.append('\n# TYPE {0} {1}\n'.format(metric.name, metric.type))
           for name, labels, value in metric.samples:
              if labels:
                 labelstr = '{{{0}}}'.format(','.join(
                     ['{0}="{1}"'.format(
                     k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                     for k, v in sorted(labels.items())]))
              else:
                 labelstr = ''
              output.append('{0}{1} {2}\n'.format(name, labelstr, self.floatToGoString(value)))
        return ''.join(output).encode('utf-8')

	
        
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


def basic_auth_handler(url, method, timeout, headers, data, username=None, password=None):
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
    try:
      print('Listening on localhost:%s' % port)
      server = HTTPServer(('', port), RequestHandler)
      server.serve_forever() 
    except (KeyboardInterrupt, SystemExit):
        print "stop"
    finally:
        sys.exit(0)
        server.shutdown()
        server.close()


        
if __name__ == "__main__":
   print len(sys.argv)
   if len(sys.argv)==2:
     try:
        os.system("ps -ef | grep simple_http_thread  | grep -v grep |awk  '{print $2}' | xargs kill -9")
     except Exception as e:
        print e
       
   else:
     threads=[]
     try:
       for port in range(9301,9401):
           t = threading.Thread(target=start_http, args=(port, ))
           threads.append(t)
           t.daemon=True
           t.start()
     except (KeyboardInterrupt, SystemExit):
       print "Thread interuppted"


     for t in threads:
       t.join()

