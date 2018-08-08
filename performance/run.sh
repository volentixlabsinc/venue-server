#!/bin/sh

if [ "$1" == "local" ]; then
	k6 run index.js
elif [ "$1" == "docker" ]; then
	docker run  -v `pwd`:/perf -i loadimpact/k6 run /perf/index.js
elif [ "$1" == "influx" ]; then
    k6 run --out influxdb=http://localhost:8086/resultsdb index.js
else 
    echo "How To"
    echo "======"
    echo "You need to add the environment you will be running on in the command line."
    echo "For example: ./run.sh local"
    echo "You have 3 choices:"
    echo "  local: The output will be your console. You need K6 installed."
    echo "  docker: The output will be your console. You need Docker installed."
    echo "  influx: The output will be driven to a local influxDB. You need influx db for this."
fi