#!/bin/bash
cd /code && python manage.py collectstatic --noinput
cd /code && python manage.py collectmedia --noinput
cd /code && python manage.py migrate
exec "$@"
