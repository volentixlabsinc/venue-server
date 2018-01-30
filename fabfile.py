from fabric.api import env, run, sudo, put, local, open_shell
from fabric.contrib.project import rsync_project
from fabric.contrib.files import is_link
from fabric.context_managers import cd

BASE_DIR = '/home/ubuntu'
DB_NAME = 'volentix'
DB_USER = 'volentix'
DB_PASSWORD = 'BxKkpaihl67B'

env.user = 'ubuntu'
env.hosts = ['45.32.186.213']
env.port = 45976

def uname():
    run('uname')

def sync():
    """ Syncs the code to the remote server """
    local('python manage.py collectstatic --no-input')
    exc = [
        '*.pyc', '.DS_Store', '*.pid', '*.log.*', 'media', '__pycache__',
        '*~', '.git', '.gitignore', '*.log', 'logs', 'celerybeat-schedule'
        '*.rdb', '*.sqlite3', '*.dump', 'node_modules'
    ]
    rsync_project(BASE_DIR, delete=False, exclude=exc, ssh_opts='-o stricthostkeychecking=no')

def setup_server():
    """ Installs required Ubuntu packages """
    sudo('apt-get update')
    cmd = 'apt-get -y install python-dev python-pip nginx '
    cmd += 'postgresql libpq-dev postgresql-client postgresql-client-common '
    cmd += 'libncurses5-dev libev-dev redis-server'
    sudo(cmd)

def setup_nginx():
    """ Configures nginx webserver """
    default_server = '/etc/nginx/sites-enabled/default'
    if is_link(default_server):
        sudo('rm ' + default_server)
    project_server = '/etc/nginx/sites-enabled/volentix_venue'
    if not is_link(project_server):
        sudo('cp %s/volentix_venue/nginx/volentix.conf /etc/nginx/sites-available/volentix' % BASE_DIR)
        sudo('ln -s /etc/nginx/sites-available/volentix /etc/nginx/sites-enabled/')
        sudo('cp %s/volentix_venue/nginx/flower.conf /etc/nginx/sites-available/flower' % BASE_DIR)
        sudo('ln -s /etc/nginx/sites-available/flower /etc/nginx/sites-enabled/')
    sudo('service nginx restart')

def setup_database():
    """ Create the database in postgres """
    cmd = '''psql -t -A -c "ALTER USER postgres WITH PASSWORD '%s';"''' % DB_PASSWORD
    run('sudo -i -u {} '.format(DB_USER) + cmd)
    cmd = 'createdb %s' % DB_NAME
    run('sudo -i -u %s '.format(DB_USER) + cmd)
    with cd(BASE_DIR + '/volentix_venue'):
        run('python manage.py migrate')
        run('python manage.py createsuperuser')

def run_app():
    """ Runs the programs required by the web application """
    with cd(BASE_DIR + '/volentix_venue'):
        run('supervisord')

def restart(program):
    """ Restarts a given program """
    with cd(BASE_DIR + '/volentix_venue'):
        run('supervisorctl restart ' + program)

def stop_app(program):
    """ Stops all the programs that power the web application """
    with cd(BASE_DIR + '/volentix_venue'):
        run('supervisorctl stop ' + program)
