#!/usr/bin/env python

import argparse

# Open a file for writing. Use 'a' instead of 'w' to append to the file.

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--interval", type=int,
                    default=10, help="Alert rule eval interval in seconds")
parser.add_argument("-s", "--start_port", type=int,
                    default=9300, help="First port #")
parser.add_argument("-m", "--metrics_per_port", type=int,
                    default=100, help="# of metrics per port")
parser.add_argument("num_proc", type=int, default=1,
                    help="Number of processes. ")
parser.add_argument("ports_per_proc", type=int, default=100,
                    help="Number of ports per process")
args = parser.parse_args()

rec_file = open('record-rules.yml', 'w')

rec_file.write("groups: \n")

count = 0
for k in range(args.metrics_per_port):
    mname = "node_" + str(k) + "_total"
    if k % args.num_proc == 0:
        rec_file.write("  - name: sa-1m-aggr-%d\n" % (count))
        rec_file.write("    interval: 1m\n")
        rec_file.write("    rules:\n")
        count += 1
    rec_file.write('      - record: %s:avg:1m\n' % (mname))
    rec_file.write('        expr: avg_over_time(%s[1m])\n' % (mname))
    rec_file.write('      - record: %s:max:1m\n' % (mname))
    rec_file.write('        expr: max_over_time(%s[1m])\n' % (mname))
    rec_file.write('      - record: %s:min:1m\n' % (mname))
    rec_file.write('        expr: min_over_time(%s[1m])\n' % (mname))
    rec_file.write('      - record: %s_missing\n' % (mname))
    rec_file.write('        expr: count_over_time(%s[1m])\n' % (mname))
    rec_file.write('\n')

# Close the file because we are done with it.
rec_file.close()

alert_file = open('alert-rules.yml', 'w')

alert_file.write("groups: \n")

count = 0
for k in range(args.metrics_per_port):
    mname = "node_" + str(k) + "_total"
    if k % args.num_proc == 0:
        alert_file.write("  - name: sa-alert-%d\n" % (count))
        alert_file.write("    interval: %ss\n" % (args.interval))
        alert_file.write("    rules:\n")
        count += 1
    alert_file.write('      - alert: %s_high\n' % (mname))
    alert_file.write('        expr: %s > 400\n' % (mname))
    alert_file.write('        for: 10s\n')
    alert_file.write('        labels:\n')
    alert_file.write('          severity: page\n')
    alert_file.write('        annotations:\n')
    alert_file.write('          summary: High\n')
    alert_file.write('\n')

# Close the file because we are done with it.
alert_file.close()
