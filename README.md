# venue-server

[![CircleCI](https://circleci.com/gh/Volentix/venue-server.svg?style=shield&circle-token=3467557bd2b7ccdcfe95bc5025d053f70adc3292)](https://circleci.com/gh/Volentix/venue-server)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![standard-readme compliant](https://img.shields.io/badge/standard--readme-OK-green.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)
[![MIT](https://img.shields.io/github/license/mashape/apistatus.svg)](https://choosealicense.com/licenses/mit/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Open Source Love](https://badges.frapsoft.com/os/v3/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)

> The backend services for the Venue, a community engagement platform for the Volentix community    

Need A LONGER DESCRIPTION HERE!!!!!!!!!!
?? Autonomous signature campaign tracking

## Table of Contents

- [Install](#install)
- [Usage](#usage)
  - [Testing](#testing)
  - [Running](#running)
- [Maintainers](#maintainers)
- [Contribute](#contribute)
- [License](#license)

## Install

Before running Venue, make sure you have the following installed on your machine.

  * [Docker](https://www.docker.com/)
  * [Docker Compose](https://docs.docker.com/compose/)
  * [Python 3](https://www.python.org/download/releases/3.0/)
  * [Pip](https://pip.pypa.io/en/stable/)

## Usage

### Testing

In order to run the tests locally, you will need to set up the projects dependancies.
```
pip install -r requirements.txt
```

Add the Supervisor:
```
pip install git+https://github.com/Supervisor/Supervisor
```

Run the tests.
```
?????? NEED THE COMMAND TO RUN THE TESTS
```
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
  * **User:** Admin
  * **Password:** default2018
```
http://localhost:8000/admin
```

See the docs:
```
http://localhost:8000/docs/
```

See the api:
```
http://localhost:8000/api/
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
