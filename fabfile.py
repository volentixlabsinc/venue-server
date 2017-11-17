from fabric.api import env, run, sudo, put, local, open_shell
from fabric.contrib.project import rsync_project
from fabric.context_managers import cd

BASE_DIR = '/home/ubuntu'
env.user = 'ubuntu'
env.hosts = ['45.32.186.213']
env.port = 45976

def uname():
    run('uname')

def sync():
    local('python manage.py collectstatic --no-input')
    exc = [
            '*.pyc','.DS_Store', '*.pid', '*.log.*', 'media', '__pycache__',
            '*~','.git','.gitignore','*.log', 'logs', 'celerybeat-schedule'
            '*.rdb', '*.sqlite3', '*.dump', 'node_modules'
        ]
    rsync_project(BASE_DIR, delete=False, exclude=exc,
        ssh_opts='-o stricthostkeychecking=no')

def restart(program):
    with cd(BASE_DIR + '/volentix'):
        run('supervisorctl restart ' + program)