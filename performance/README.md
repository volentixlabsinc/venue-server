# Venue-Server Performance

> This is the performance test suite for Venue.

The following package contains the artifacts and logic to run performance testing against the venue-server API. It uses [K6](https://k6.io/) as the engine and, optionally, influxd/grafana as its metrics monitoring solution.

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Adding Tests](#adding-tests)

## Install

This suite supports three ways of running the performance suite, depending on what your needs are. The options are:

  * Docker: Requires [Docker](https://www.docker.com/)
  * local:  Requires [K6](https://k6.io/)
  * influx: Requires [K6](https://k6.io/) and [InfluxDB](https://docs.influxdata.com/influxdb/v1.6/introduction/installation/)

**Note**: If you are using the influx varient of the tool, you will also want to install [Grafana](https://grafana.com/) in order to visualize the output. [This artice](https://medium.com/codeinsights/how-to-load-test-your-node-js-app-using-k6-74d7339bc787) gives a good overview.
  
## Usage

Change directory into the performance folder.

**Docker**

All output will be sent to stdout.

To Run:
```
bash ./run.sh docker
```

**Local**

All output will be sent to stdout.

To Run:
```
bash ./run.sh local
```

**influx**

Metrics will be sent to influx at: localhost:8086/resultsdb

To Run:
```
bash ./run.sh influx
```

## Adding Tests

This project leverages the code of others. You can check out the original structure, as well as documentation [on their github site](https://github.com/bamlab/performance-monitoring).

Adding tests, in order to run with the rest of the suite, requires a little bit of configuration.

  1. Create the test. See the (basic)(workflows/basic.js) file. Note that it extends BaseTest and manages its configuration in the parent dir files.
  2. Add it to the (index.js)[index.js] file.

