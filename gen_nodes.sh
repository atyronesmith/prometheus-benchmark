#!/bin/sh

if [ $# -lt 1 ] 
  then
    echo "Generate Prometheus node.yml file(s)"
    echo " The node-x.yml file specifies a number of target nodes"
    echo " to scrape.  This program generates one or more node-x.yml"
    echo " files that are invoked by associated jobs in the prometheus.yml file."
    echo " The number of files generated is equal to the number proccess used "
    echo " by the shtp.py program.  "
    echo " "
    echo "Usage: $0 num_processes ports_per_process [ start_port ]"
    echo " "
    echo " num_processes - specified by the -m N parameter to shtp.py "
    echo " ports_per_process - specified by the num_ports parameter to shtp.py"
    echo " start_port - defaults to 9300 "
    exit 1
fi
num_procs=$1
ports_pp=$2
start_port=9300

echo "Number of procs: " ${num_procs}
echo "Ports per proc: " ${ports_pp}

if [ -n "$3" ]; 
  then
    start_port = $32
fi

for ((i=0;i<$num_procs;i++))
  do 
     fname="nodes/nodes-$((${i}+1)).yml"
     echo "- targets:" > ${fname}

     for ((j=0; j<${ports_pp}; j++))
       do
         echo "  - localhost:$(expr ${start_port} + ${j} )" >> ${fname}
     done
     start_port=$((${start_port}+${ports_pp}))
     echo "start_port = ${start_port}"
  done

