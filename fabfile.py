from fabric.api import env, run, sudo, put, local, open_shell
from fabric.contrib.project import rsync_project
from fabric.contrib.files import is_link
from fabric.context_managers import cd


BASE_DIR = '/home/ubuntu'
env.user = 'ubuntu'
env.hosts = ['45.32.186.213']
env.port = 45976


def uname():
    run('uname')


def setup_nginx():
    """ Configures nginx webserver """
    default_server = '/etc/nginx/sites-enabled/default'
    if is_link(default_server):
        sudo('rm ' + default_server)
    project_server = '/etc/nginx/sites-enabled/venue'
    if not is_link(project_server):
        sudo('cp %s/venue-server/nginx/venue.conf /etc/nginx/sites-available/venue' % BASE_DIR)
        sudo('ln -s /etc/nginx/sites-available/venue /etc/nginx/sites-enabled/')
        sudo('cp %s/venue-server/nginx/flower.conf /etc/nginx/sites-available/flower' % BASE_DIR)
        sudo('ln -s /etc/nginx/sites-available/flower /etc/nginx/sites-enabled/')
    sudo('service nginx restart')
    # Note: HTTPS still needs to be manually set up on the server


def run_app():
    """ Runs the application on the remote server """
    with cd(BASE_DIR + '/venue-server'):
        run("sed -i '--' 's/DEBUG = True/DEBUG = False/g' volentix/settings.py")
        run('docker rm venue-server_web_1 -f')
        run('docker-compose up -d')
        sudo('service nginx restart')


def sync():
    """ Syncs the code to the remote server """
    local('python manage.py collectstatic --no-input')
    exc = [
        '*.pyc', '.DS_Store', '*.pid', '*.log.*', 'media', '__pycache__',
        '*~', '.git', '.gitignore', '*.log', 'logs', 'celerybeat-schedule'
        '*.rdb', '*.sqlite3', '*.dump', 'node_modules'
    ]
    # Sync code with the remote server
    rsync_project(
        BASE_DIR,
        delete=False,
        exclude=exc,
        ssh_opts='-o stricthostkeychecking=no'
    )
    # Run the app
    # run_app()
