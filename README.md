# venue-server

> Autonomous signature campaign tracking

### Setup for local development

##### *1. Install Docker Community Edition (CE)*
    1. Download the installer for your OS from the page below:<br>
        https://www.docker.com/community-edition
    2. Run/execute the installer
##### *2. Get a copy of the source code into your local*
    1. Clone this repo from github: `git clone <url-of-this-repo>`
    2. Change directory to the root of the project: `cd venue-server`
##### *3. Run the API server application and check in the browser*
    1. Run `docker-compose up`. In Linux, it may be necessary to use sudo, so you'll have to run `sudo docker-compose up`
    2. The API docs should be accessible here: http://localhost:8000/docs/
    3. If you're developing the frontend, make sure you set your API base URL to http://localhost:8000
##### *4. Run the provided reference frontend*
    1. Change directory to `venue_app`
    2. Install npm packages by running `yarn`
    3. Run the app with `npm run dev`
    4. Load the app at this URL: http://localhost:8080
#### *5. Login as the test user*
    * The test user credentials is:<br>
    username: joemar.ct
    password: default2018 


### Rebuilding the web image and recreating the containers
**Note: In certain cases, you might need to recreate the docker containers from scratch (which will also wipe your DB clean). If that is needed, this is how you do that:
```
On the `venue-server` base directory, run these commands in sequence:
1. `docker-compose down`
2. `docker-compose build web`
3. `docker-compose up` 
```

### Deployment to remote server

Note: This only works in Ubuntu/Unix machines because `fab sync` command uses command line `rsync` program, which has no Windows equivalent.

##### *1. Spin up a server and install Docker CE*
    1. Spin up a clean Ubuntu 16.04 LTS server (preferrably one that has Docker CE preinstalled)
    2. Connect by SSH to the server
    2. Install Docker CE (if not installed yet) using the command:<br>
       `curl -fsSL https://get.docker.com | sh`
##### *2. Edit the `fabfile.py` file:*
    1. Upate the `env.hosts` variable by replacing the IP in the existing list with the IP of the Ubuntu server
    2. Update the `env.port`, if necessary
    3. Test that the fab commands are working, try with `fab uname`
    4. If the command is working, proceed to the next step
##### *3. Sync the code to the server then run the application:*
    1. Sync the source code to the server with command `fab sync`
    2. Run the application on the remote server with `fab run_app`
    3. Open the site in the browser: https://venue.volentix.com

