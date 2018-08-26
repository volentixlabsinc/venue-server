#!/bin/sh
cd /code && python manage.py collectstatic --noinput
cd /code && python manage.py migrate
cd /code && python manage.py loaddata fixtures/*.json
exec "$@"
