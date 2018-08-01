# venue-server

[![CircleCI](https://circleci.com/gh/Volentix/venue-server.svg?style=shield&circle-token=3467557bd2b7ccdcfe95bc5025d053f70adc3292)](https://circleci.com/gh/Volentix/venue-server)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![standard-readme compliant](https://img.shields.io/badge/standard--readme-OK-green.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)
[![MIT](https://img.shields.io/github/license/mashape/apistatus.svg)](https://choosealicense.com/licenses/mit/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Open Source Love](https://badges.frapsoft.com/os/v3/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)

> The backend services for Venue, a community engagement platform for the Volentix community

With Venue, members can post campaigns and bounties for work needed -- for example, fixing bugs, creating content, or promoting Volentix -- and anyone may claim a bounty in exchange for their efforts. Venue provides real time metrics on VTX rewards earned by participants and incentivizes the adoption of VTX.

This backend is a REST API server which receives, processes, and/or serves data for the Venue frontend.

The major dependencies are:
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
- [Bitcointalk Signature Campaign](#bitcointalk-signature-campaign)
  - [Forum Account Verification](#forum-account-verification)
  - [Points System](#points-system)
  - [Scraping and Calculations](#scraping-and-calculations)
- [Maintainers](#maintainers)
- [Contribute](#contribute)
- [License](#license)

## Install

Before running Venue, make sure you have the following installed on your machine.

  * [Docker](https://www.docker.com/) (tested with version 18.03.1-ce)
  * [Docker Compose](https://docs.docker.com/compose/) (if not installed along with Docker, tested with version 1.21.1)

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




## Bitcointalk Signature Campaign

The first ever campaign launched in Venue is a signature campaign in Bitcointalk.org forum site. In this campaign, users who have accounts in the forum can sign up in Venue and join the campaign where it is possible to choose from a selection of signature codes. The code is a BBCode for a Volentix ad banner, which will be shown as signature in each of the user's posts and the user earns VTX tokens as a reward.

Only members of the higher Bitcointalk positions are allowed to participate in the campaign -- namely Member, Full Member, Sr. Member, Hero, and Legendary.

### Forum Account Verification

When a Venue user joins the campaign, he/she will be asked for Bitcointalk user ID. The system validates this ID -- checks if it exists and if the position is high enough to be allowed to participate in the campaign. When allowed, the user is asked to choose a signature. The code for the selected signature then needs to be copied and placed in the user's Bitcointalk profile. The system then verifies the placement of the signature. The integrity of the signature placed in the profile is checked simply by checking if it contains the expected links.

### Points System

The campaign is pre-set to have a fixed amount of total VTX tokens as reward. Participants will get their share from this total reward proportional to their number of posts plus some bonus according to their forum positions. This is all tracked using a point system, which is described below.

Some settings that affect the behavior of point system are made configurable through the admin interface (`/admin/constance/config/`):

1. `VTX_AVAILABLE` [default: 120,000] - Total VTX tokens available
2. `POST_POINTS_MULTIPLIER` [default: 100] - Points for each new post
3. `MATURATION_PERIOD` [default: 24] - Post maturation period in hours
4. `UPTIME_PERCENTAGE_THRESHOLD` [default: 90] - Percentage of uptime required

This is how the point system works:

Every new post by a user that bears the signature is automatically credited 100 base points (defined by `POST_POINTS_MULTIPLIER`) plus bonus points, which is a percentage of the base points based on the user's forum position. This new post is monitored roughly every 5 minutes for up to 24 hours (`MATURATION_PERIOD`) to check for signature removal. The time elapsed when the signature is not found is recorded as invalid signature minutes (i.e. signature downtime). If the signature downtime exceeds a threshold, the points for the post is removed.

The downtime threshold is 100 minus `UPTIME_PERCENTAGE_THRESHOLD` percent of the `MATURATION_PERIOD`.

The bonus points percentage are as follows:

1. Member - no bonus
2. Full Member - 1%
3. Sr. Member - 2%
4. Hero/Legendary - 5%

### Scraping and Calculations

Scraping of the users' profiles and their posts in Bitcointalk is done regularly in the background at a regular interval of roughly 5 minutes. Upon completion of every scraping round, the total points are calculated which is the basis for the ranking and the dynamic computation of VTX tokens earned by each user. All these cascade of background tasks are executed automatically by a periodic call to the `update_data()` function in `venue/tasks.py`.

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
