
from prometheus_client import start_http_server,CollectorRegistry,Gauge,Metric
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
import json
import requests
import sys
import time
import collections
import random
import threading
import socket
import time
import signal
import sys
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import logging
import datetime
import daiquiri
import threading
import os
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )
daiquiri.setup(
    level=logging.DEBUG,
    outputs=(
        daiquiri.output.File('prometheus.log', level=logging.ERROR),
        daiquiri.output.TimedRotatingFile(
            'everything.log',
            level=logging.DEBUG,
            interval=datetime.timedelta(hours=8))
    )
)
LOG = daiquiri.getLogger(__name__)
class MyCollector(object):
  def __init__(self,port):
      self.port = port
  #def describe(self):
  #    metric=[]
  #    for index in range(index):
  #      metric.append(GaugeMetricFamily("svcs_"+str(index)+"_"+ str(self.port)+"_documents_loaded", 'Help text', value=random.random()))

	
  def collect(self):
      index=100
      try:
        for index in range(index):
          yield GaugeMetricFamily("svcs_"+str(index)+"_"+ str(self.port)+"_documents_loaded", 'Help text', value=random.random())
          #data={"fast": random.random(),"slow": random.random()} 
          #metric = Metric("svcs_"+str(index)+"_"+ str(self.port)+"_documents_loaded", 'Requests failed', 'gauge')
          #for k, v in data.items():
          #    metric.add_sample("svcs_"+str(index)+"_"+ str(self.port)+"_documentes_loaded",
          #	 value=v, labels={'repository': k})
          #yield metric
      except Exception as e:
        print "ERRRRRRRRRRRRRRRRR"
        print e
	LOG.error(e)

       #for metric in self.metric_name_list:
          #metric.set(float(random.random()))
          #metric.set_to_current_time()   # Set to current unixtime
       #   yield metric


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
def signal_term_handler(signal, frame):
    print "closing"

def start_http(port):
    # Create the registry
    print "starting  port" + str(port)
    from prometheus_client.core import REGISTRY
 
    try:
      myCollector=MyCollector(port)
      reg=CollectorRegistry(auto_describe=True)
      reg.register(myCollector)
     
      def handler(*args, **kwargs):
          MyMetricHandler(reg, *args, **kwargs)
      #server=start_http_server(port,handler)
      #myCollector=MyCollector(port)
      #reg=CollectorRegistry(auto_describe=True)
      #reg.register(myCollector)
      server = HTTPServer(('', port), handler)
      server.serve_forever()      
      #while True: time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
	print "stop"
    finally:
        sys.exit(0)
        server.shutdown()
        server.close()

class MyMetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler that gives metrics from ``core.REGISTRY``."""
    def __init__(self, registry, *args, **kwargs):
        self.registry = registry

        super().__init__(*args, **kwargs)

    def do_GET(self):
        registry = core.REGISTRY
        params = parse_qs(urlparse(self.path).query)
        if 'name[]' in params:
            registry =self.registry.restricted_registry(params['name[]'])
        try:
            output = generate_latest(registry)
        except:
            self.send_error(500, 'error generating metric output')
            raise
        self.send_response(200)
        self.send_header('Content-Type', CONTENT_TYPE_LATEST)
        self.end_headers()
        self.wfile.write(output)

    def log_message(self, format, *args):
        """Log nothing."""

if __name__ == "__main__":
   if len(sys.argv)==2:
     try:
      os.system("ps -ef | grep prometheus_test.py | grep -v grep |awk  '{print $2}' | xargs kill -9")
     except:
       pass
   else: 

     threads=[]   
     try:
       for port in range(9301,9401):
           t = threading.Thread(target=start_http, args=(port, ))
           threads.append(t)
           #t.daemon=True
           t.start()
     except (KeyboardInterrupt, SystemExit):
       print "Thread interuppted" 
 

     for t in threads:
       t.join()




         

