from fabric.operations import local, put, run, env, sudo, get
from fabric.context_managers import cd, lcd
import os

# to run:
#    fab <env> <function>:<system>

def qa():
    env.user = 'root'
    env.my_name = 'QA'
    env.hosts = ['104.236.250.57']
    env.password = 'CustomSoftHer0!'


def live():
    env.user = 'root'
    env.my_name = 'LIVE'
    env.hosts = ['178.62.83.205']
    env.password = 'CustomSoftHer0!'

def test():
    print 'my_name', env.my_name 

def collect():
    local('tar -cvzf /tmp/onlinejp.tbz -X exclude.txt .')
    put('/tmp/onlinejp.tbz', '/srv/')
    local('rm /tmp/onlinejp.tbz')
    
def create():
    with cd('/srv/'):
        run('rm -rf onlinejp/ && mkdir onlinejp/')
        run('mv onlinejp.tbz onlinejp/')
    with cd('/srv/onlinejp/'):
        run('tar -xvzf onlinejp.tbz')
        run('rm onlinejp.tbz')
        for cmd in ('log','run'):
            run('mkdir {}'.format(cmd))

def setup():
    with cd('/srv/onlinejp/'):
        run('source /py2env/bin/activate && '\
            'pip install -r requirements.txt')
        if env.my_name == 'QA':
            run('cp qa_settings.py settings.py')
            run('cp onlinejp.qa.nginx '\
                   '/etc/nginx/sites-available/onlinejp.nginx')
        elif env.my_name == 'LIVE':
            run('cp live_settings.py settings.py')
        run('cp onlinejp.conf /etc/supervisor/conf.d')

def restart():
    run('sudo supervisorctl reread')
    run('sudo supervisorctl update')
    run('sudo supervisorctl restart onlinejp')
    run('sudo service nginx restart')

def get_db():
    run('tar -czvf yourcv.tbz /var/lib/couchdb/yourcv.couch')
    get('yourcv.tbz')
    # TODO: local('echo "fr3dalex\n" | sudo tar -xzvf youcv.tbz')
    # TODO: local('rm youcv.tbz')

def put_db():
    local('echo "fr3dalex\n" |'\
          ' sudo tar -czvf onlinejp.tbz /var/lib/couchdb/onlinejp.couch')
    put('onlinejp.tbz', '/tmp/')
    run('tar -xzvf /tmp/onlinejp.tbz -C /var/lib/couchdb --strip-components=1')
    run('rm /tmp/onlinejp.tbz')
        
def deploy(withdata=False):
    collect()
    create()
    setup()
    restart()
    if withdata:
        put_db()

