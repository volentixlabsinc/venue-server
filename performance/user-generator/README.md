# venue-user-generator

> Generates the records for a preset number of users.

This tool is for the generation of users, and their associated records, in order to quickly create a large volume of records.

## Table of Contents

- [Install](#install)
- [Usage](#usage)

## Install

Install is trivial:

```
npm install
```

## Usage

To use the generator, you simply run the following command, which generates 10 users.

```
node all.js
```

If you wish to generate a different number of users, just add the USERS env var.

```
USERS=30 node all.js
```

Once the application has ran, a new file will be generated, in this folder, called: 0002_auto_20180710_0208.py

You can then move this file into the venue/migrations/ folder.

Before you launch, you may want to stop and remove all docker containers.

```
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
```

Now you simply launch the application, from the root folder:

```
docker-compose up
```

