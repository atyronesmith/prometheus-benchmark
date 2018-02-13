#!/bin/sh

if [ $# -lt 2 ] 
  then
    echo "Generate Prometheus nodes/node-XX.yml file(s)"
    echo " The nodes/node-XX.yml file(s) specify a number of target nodes"
    echo " to scrape.  This program generates one or more nodes/node-XX.yml"
    echo " files that are invoked by associated jobs in the prometheus.yml file."
    echo " The number of files generated is equal to the number proccess used "
    echo " by the shtp.py program.  "
    echo " "
    echo " The jobs.yml file is generated along with the node files.  The jobs.yml"
    echo " file specifies a job entry for each num_processes.  "
    echo " if the -u flag is include, the local ./prometheus.yml file is updated with"
    echo " the contenst of the jobs.yml files."
    echo " "
    echo " A record-rules.yml file is also generated.  The file will contain 3 recording rules"
    echo " for each timeseries (metric).  The recording rule creates a new series with 1m"
    echo " granularity for avg, max, min.  The rules are to simulated the processing needed"
    echo " to downsample data to 1m granularity."
    echo " "
    echo "Usage: $0 [-p start_port] [-a ip_address] [-m no_metrics] num_processes ports_per_process"
    echo " "
    echo " num_processes - specified by the -m N parameter to shtp.py "
    echo " ports_per_process - specified by the num_ports parameter to shtp.py"
    echo " -p start_port  start port (default 9300) "
    echo " -a ip_addr     ip address of the scrape targets (default localhost)"
    echo " -u             update the local prometheus.yml file with the jobs.yml content"
    echo " -m no_metrics  number of metrics per port (default 100)"
 
    exit 1
fi

f_nodes_base_name="nodes/nodes-"
f_jobs_name="jobs.yml"
f_rules_name="record-rules.yml"
f_alert_rules_name="alert-rules.yml"

STARTPORT=9300
IPADDR="localhost"
UPDATE=0
METRICSPERPORT=100

while getopts ":a:p:um:" option
do
 case "${option}"
 in
 a) IPADDR=${OPTARG};;
 p) STARTPORT=${OPTARG};;
 u) UPDATE=1;;
 m) METRICSPERPORT=${OPTARG};;
 esac
done
shift $((OPTIND-1))

num_procs=$1
ports_pp=$2

echo "Number of procs: " ${num_procs}
echo "Ports per proc: " ${ports_pp}

echo "# AUTO-GENERATED jobs" > ${f_jobs_name}

start_port=${STARTPORT}
for ((i=0;i<$num_procs;i++))
  do
     foffset=$((${i}+1)) 
     fname="${f_nodes_base_name}${foffset}.yml"
     echo "- targets:" > ${fname}

     echo "Writing...${fname}, ${IPADDR}:${start_port}"
     for ((j=0; j<${ports_pp}; j++))
       do
         echo "  - \"${IPADDR}:$(expr ${start_port} + ${j} )\"" >> ${fname}
     done

     echo "  - job_name: 'sa-${foffset}'" >> ${f_jobs_name}
     echo "    file_sd_configs:" >> ${f_jobs_name}
     echo "      - files:" >> ${f_jobs_name}
     echo "        - ${fname}" >> ${f_jobs_name}
   

     start_port=$((${start_port}+${ports_pp}))
  done

  if [ "${UPDATE}" -eq "1" ] && [ -f prometheus.yml ]; then
     sed -i -n '/# AUTO-GENERATED jobs/q;p' prometheus.yml 
     cat jobs.yml >> prometheus.yml 
  fi

cat <<EOT > ${f_rules_name}
groups: 
  - name: sa-1m-aggr
    interval: 1m
    rules:
EOT

num_rules=$(( ${num_procs}*${ports_pp}*${METRICSPERPORT}*3 ))
echo "Adding ${num_rules} to ${f_rules_name}"
start_port=${STARTPORT}
total_rules=0
for ((i=0;i<$num_procs;i++))
  do 
    for ((j=0; j<${ports_pp}; j++))
      do
        for ((k=0; k<${METRICSPERPORT}; k++))
          do
            cport=$(expr ${start_port} + ${j})
            mname="svcs_${cport}_${k}_total"
cat <<EOT >> ${f_rules_name}
        - record: ${mname}:avg:1m
          expr: avg_over_time(${mname}[1m])
        - record: ${mname}:max:1m
          expr: max_over_time(${mname}[1m])
        - record: ${mname}:min:1m
          expr: min_over_time(${mname}[1m])

EOT
#            echo "      - record: ${mname}:cnt:1m" >> ${f_rules_name}
#            echo "        expr: count_over_time(${mname}[1m])" >> ${f_rules_name}
#            echo "      - record: ${mname}:std:1m" >> ${f_rules_name}
#            echo "        expr: stddev_over_time(${mname}[1m])" >> ${f_rules_name}
#            echo " ">> ${f_rules_name}
          done
      done
     total_rules=$(( ${total_rules}+(${METRICSPERPORT}*${ports_pp}*3)))
     echo -ne "\r${total_rules}       "
     start_port=$((${start_port}+${ports_pp}))
  done

echo " "

cat <<EOT > ${f_alert_rules_name}
groups:
  - name: sa-alert
    rules:
EOT

num_rules=$(( ${num_procs}*${ports_pp}*${METRICSPERPORT} ))
echo "Adding ${num_rules} to ${f_alert_rules_name}"
start_port=${STARTPORT}
total_rules=0
for ((i=0;i<$num_procs;i++))
  do 
    for ((j=0; j<${ports_pp}; j++))
      do
        for ((k=0; k<${METRICSPERPORT}; k++))
          do
            cport=$(expr ${start_port} + ${j})
            mname="svcs_${cport}_${k}_total"
cat <<EOT > ${f_alert_rules_name}
      - alert: ${mname}_high" >> ${f_alert_rules_name}
        expr: ${mname} > 10" >> ${f_alert_rules_name}
        for: 10s" >> ${f_alert_rules_name}
        labels:" >> ${f_alert_rules_name}
          severity: page" >> ${f_alert_rules_name}
        annotations:" >> ${f_alert_rules_name}
         summary: High value" >> ${f_alert_rules_name}

EOT
          done
      done
     total_rules=$(( ${total_rules}+(${METRICSPERPORT}*${ports_pp})))
     echo -ne "\r${total_rules}       "
     start_port=$((${start_port}+${ports_pp}))
  done
 

echo " "

