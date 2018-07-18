# venue-server

[![standard-readme compliant](https://img.shields.io/badge/standard--readme-OK-green.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)
[![Semver](http://img.shields.io/SemVer/2.0.0.png)](http://semver.org/spec/v2.0.0.html)
[![Open Source Love](https://badges.frapsoft.com/os/v3/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)
[![MIT](https://badges.frapsoft.com/os/mit/mit.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

> The backend services for the Venue rewards and bounty tracker platform.    

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
  * [Pyton 3](https://www.python.org/download/releases/3.0/)
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

## Contribute

See [the contribute file](contribute.md)!

PRs accepted.

Small note: If editing the README, please conform to the [standard-readme](https://github.com/RichardLitt/standard-readme) specification.

## License

MIT © 2018 Volentix Labs Inc
