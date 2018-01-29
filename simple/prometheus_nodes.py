# Set the python path
import inspect
import os
import sys

import threading
from http.server import HTTPServer
import socket
import time

from prometheus.collectors import Gauge
from prometheus.registry import Registry
from prometheus.exporter import PrometheusMetricHandler
import psutil
from multiprocessing import Pool
import daiquiri

def gather_data(registry):
    """Gathers the metrics"""
    host = socket.gethostname()
    metric_name_list=[]
    metrics={} 
    for index in range(100):
       metric_name_list.append("metric_"+str(index)) 
       metrics["metric_"+str(index)]= Gauge("metric_"+str(index), "fake metrics.",{'host': host})
       registry.register("metric_"+str(index))

    # register the metric collectors
    registry.register(ram_metric)
    registry.register(cpu_metric)

    # Start gathering metrics every second
    while True:
        time.sleep(1)

        # Add ram metrics
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()

        ram_metric.set({'type': "virtual", }, ram.used)
        ram_metric.set({'type': "virtual", 'status': "cached"}, ram.cached)
        ram_metric.set({'type': "swap"}, swap.used)

        # Add cpu metrics
        for c, p in enumerate(psutil.cpu_percent(interval=1, percpu=True)):
            cpu_metric.set({'core': c}, p)
def start_http(port):
    # Create the registry
    registry = Registry()

    try:
        # We make this to set the registry in the handler
        def handler(*args, **kwargs):
            PrometheusMetricHandler(registry, *args, **kwargs)

        server = HTTPServer(('', port), handler)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

    
   
def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

if __name__ == "__main__":
    if len(sys.argv)<2 :
       print "Please pass no of servers. usage script.py 10"
       exit(1)
    no_of_server = int(sys.argv[1])
    pool=Pool(10,init_worker)
    ports = []
    for index in range(no_of_server):
        ports.append(9200+ index)
    try:
        res = pool.map_async(start_http, ports,1)
        print "Result"
        res.wait()

    except KeyboardInterrupt:
       print "Keyboard interuppted"
       pool.terminate()
    else:
       pool.close()

    pool.join()


