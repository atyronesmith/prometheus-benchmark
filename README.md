# prometheus-benchmark
Files related to the bench-marking of prometheus

simple/ -- older, lower performing tests
multi-process/ -- attempt at increasing performance through multi-process
shtp.py -- Current benchmarking python
gen_nodes.sh -- generate nodes for configuration of the Promtheus DUT
nodes.yaml -- sample file that defines targets


shtp.py -h

usage: shtp.py [-h] [-m MPROC_COUNT] [-t TIME] [-s START_PORT]
               [--metric_count METRIC_COUNT]
               port_count

positional arguments:
  port_count            Create port_count endpoints

optional arguments:
  -h, --help            show this help message and exit
  -m MPROC_COUNT, --mproc_count MPROC_COUNT
                        Number of processes to create, threads will be evently
                        spread across processes
  -t TIME, --time TIME  Number of seconds to run
  -s START_PORT, --start_port START_PORT
                        First port #
  --metric_count METRIC_COUNT
                        # of metrics per node
 

 This program simulates multiple targets (nodes) for scraping by Prometheus.  

example:
   python shtp.py -m 10 -t 60 -s 9301 --metric_count 100 500

This will start a test target simulator using 10 processes with
50 simulated nodes per process.  To benchmark prometheus, modify
your prometheus.yml to use a target include file and then generate
a nodes.yml file and place in nodes/ directory.

....
  - job_name: 'test_nodes'

    scrape_interval: 1s

    file_sd_configs:
      - files:
        - 'nodes/nodes.yml'
...


gen_nodes.sh 500

produces 

- targets:
  - localhost:9301
  - localhost:9302
  - localhost:9303
  - localhost:9304
  - localhost:9305
  - localhost:9306
  - localhost:9307
  - localhost:9308
  - localhost:9309
  - localhost:9310
  - localhost:9311
  - localhost:9312
  - localhost:9313
  - localhost:9314
  - localhost:9315
  - localhost:9316
  - localhost:9317
  - localhost:9318
  - localhost:9319
  - localhost:9320
....



