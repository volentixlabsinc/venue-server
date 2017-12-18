# volentix_venue

> Autonomous signature campaign tracking

## Setup and Deployment Procedure

##### *1. Spin up a clean Ubuntu 16.04 server*
##### *2. Connect to the server through SSH, then:*
    1. Create a non-root sudo user named `ubuntu`
    2. Set the SSH access port to `45976`
    3. Add your public SSH key into the `~/.ssh/authorized_key` file to enable passwordless SSH access
##### *3. Get a copy of the source code into your local*
    1. Clone this repo from github: `git clone <url-of-this-repo>`
    2. Change directory to the root of the project: `cd volentix_venue`
##### *4. Create a virtual environment*
    1. Make sure you have Python 3.6.1+ installed
    2. Create a virtual environment: `python3 -m 'venv' ~/Environments/volentix`
    3. Activate the virtual environment: `source ~/Environments/volentix/bin/activate`
    4. Install the required Python packages: `pip install -r requirements.txt`
##### *5. Edit the `fabfile.py` file (in your local Linux/Unix machine):*
    1. Upate the `env.hosts` variable by replacing the IP in the existing list with the IP of the new server
    2. Update the `env.port`
    3. Test that the fab commands are working, try with `fab uname`
    4. If the command is working, proceed to the next steps
##### *6. Run the following commands to remotely setup the volentix_venue application:*
    1. Sync the source code to the server with command `fab sync`
    2. Setup the server: `fab setup_server`
    3. Configure nginx: `fab setup_nginx`
    4. Create database: `fab setup_database`
    5. Run the application: `fab run_app`
##### (Optional) *7. If you want to edit the Vue.js frontend app, do the following:*
    1. Change directory to venue_app: `cd venue_app`
    2. Make sure you have `npm` and `yarn` installed
    3. Install the NodeJS dependencies with `yarn install`
    4. Run the dev server with `npm run dev`
    Note: The app will connect to the live REST API server
##### (Optional) *8. When you modify the source code, you can deploy by doing the following:*
    1. Sync the source code to the server with command `fab sync`
    2. Restart all application programs with `fab restart:all`