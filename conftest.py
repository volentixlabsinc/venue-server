import pytest


@pytest.fixture(scope='session')
def celery_config():
    return {
        'broker_url': 'memory://localhost/',
        'result_backend': 'rpc',
        'task_serializer': 'pickle',
        'result_serializer': 'pickle',
        'accept_content': ['pickle']
    }


@pytest.fixture(scope='session')
def celery_worker_parameters():
    return {
        'queues':  ('celery', 'scrapers', 'control', 'mails', 'compute')
    }
