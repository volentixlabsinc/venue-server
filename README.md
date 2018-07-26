# venue-server

[![CircleCI](https://circleci.com/gh/Volentix/venue-server.svg?style=shield&circle-token=3467557bd2b7ccdcfe95bc5025d053f70adc3292)](https://circleci.com/gh/Volentix/venue-server)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![standard-readme compliant](https://img.shields.io/badge/standard--readme-OK-green.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)
[![MIT](https://img.shields.io/github/license/mashape/apistatus.svg)](https://choosealicense.com/licenses/mit/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Open Source Love](https://badges.frapsoft.com/os/v3/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)

> The backend services for Venue, a community engagement platform for the Volentix community    

This Python server provides the services for Venue. Major dependencies are:
  * [Python 3](https://www.python.org/)
  * [Django](https://www.djangoproject.com/)
  * [PostgreSQL](https://www.postgresql.org/)
  * [Redis](https://redis.io)
  * [Celery](http://www.celeryproject.org/) for asynchronous web scrapes 
  * [Docker](https://www.docker.com/)

## Table of Contents

- [Install](#install)
- [Usage](#usage)
  - [Running](#running)
  - [Troubleshooting](#troubleshooting)
  - [Testing](#testing)
- [Maintainers](#maintainers)
- [Contribute](#contribute)
- [License](#license)

## Install

Before running Venue, make sure you have the following installed on your machine.

  * [Docker](https://www.docker.com/) (tested with version 18.03.1-ce)
  * [Docker Compose (if not installed along with Docker)](https://docs.docker.com/compose/) (tested with version 1.21.1)

## Usage

### Running

Note that at the time of writting, the app does not have a set up for local development other than the docker compose script. Future iterations are expected to provide this capability.

To run the application:
```
docker-compose up
```

To recreate the docker containers from scratch and clean out the database:
```
docker-compose down
docker-compose build web
docker-compose up
```

Test the app:
```
http://localhost:8000/api/retrieve/leaderboard-data/
```

Login to the admin:
  * **User:** admin
  * **Password:** admin
```
http://localhost:8000/admin
```

See the API docs and interactive explorer:
```
http://localhost:8000/docs/
```

### Troubleshooting
#### Postgres error

If you get this error while trying to run docker on your machine:
```
postgres_1  | ERROR:  relation "venue_userprofile" does not exist at character 250
```

or

```
postgres_1  | ERROR:  relation "venue_forumprofile" does not exist at character 623
```

Try to use these commands:
```
docker-compose down -v
docker-compose up postgres
docker-compose up 
```
Docker should work well after this.

#### Docker-Isolation error

If you get this error (on Ubuntu):
```
ERROR: unable to insert jump to DOCKER-ISOLATION rule in FORWARD chain:  
(iptables failed: iptables --wait -I FORWARD -j DOCKER-ISOLATION: 
iptables v1.6.0: Couldn't load target `DOCKER-ISOLATION':
No such file or directory
```

You have to run these commands:

```
iptables -t filter -F DOCKER
iptables -t filter -X DOCKER
iptables -t filter -F DOCKER-ISOLATION
iptables -t filter -X DOCKER-ISOLATION
iptables -t nat -F DOCKER
iptables -t nat -X DOCKER-ISOLATION
```
Then you need to restart docker daemon:
```
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo systemctl daemon-reload
sudo systemctl restart docker
```
Run docker again after restarting the daemon and the error should be fixed.


### Testing

Run the tests
```
docker-compose up  # If the containers are not running yet
docker exec -it venue-server_web_1 pytest
```

## Maintainers

[@shawnlauzon](https://github.com/shawnlauzon)
[@joemarct](https://github.com/joemarct)

## Contribute

Venue is a project which was originally created by Volentix Labs, but is owned and
maintained by the Volentix community. We actively support and appreciate anyone
who wants to improve this or any project within the community.

See [CONTRIBUTING.md](https://www.github.com/Volentix/venue/CONTRIBUTING.md)

Small note: If editing the README, please conform to the [standard-readme](https://github.com/RichardLitt/standard-readme) specification.

## License

MIT © 2018 Volentix Labs Inc
