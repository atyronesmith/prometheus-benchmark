#!/bin/sh

if [ $# -lt 1 ] 
  then
    echo "Usage: $0 num_nodes [port_count]"
    exit 1
fi
num_nodes=$1
num_ports=$(expr $num_nodes + 1 )

if [ $# -eq 2 ] 
  then
   num_ports=$2
   num_ports=$(expr $num_ports + 1 )
fi

fname='nodes.yml'

cat > ${fname} <<EOF
- targets:
EOF

for i in $(seq 0 $num_nodes)
 do
   offset=$((${i} % ${num_ports}))	 
   echo "  - localhost:$(expr 9301 + ${offset} )" >> ${fname}
done

