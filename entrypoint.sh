#!/bin/bash
cd /code && python manage.py collectstatic --noinput
cd /code && python manage.py migrate
cd /code && python manage.py loaddata venue/fixtures/*.json
exec "$@"
