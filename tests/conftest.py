import pytest
from celery_app import celery_app

@pytest.fixture(autouse=True, scope="session")
def celery_eager():
    celery_app.conf.update(task_always_eager=True)
    yield
