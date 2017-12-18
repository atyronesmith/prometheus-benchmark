#!/bin/sh

if [ $# -lt 1 ] 
  then
    echo "Usage: $0 num_nodes"
    exit 1
fi

num_nodes=$1
fname='nodes.yml'

cat > ${fname} <<EOF
- targets:
EOF

for i in $(seq 1 $num_nodes)
 do
#   offset=$((${i} % 10))	 
   offset=${i}	 
   echo "  - localhost:$(expr 9300 + ${offset} )" >> ${fname}
done

