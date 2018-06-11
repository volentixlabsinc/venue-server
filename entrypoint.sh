#!/bin/bash
cd /code && python manage.py collectstatic --noinput
cd /code && python manage.py migrate
cd /code && python manage.py loaddata venue/fixtures/*.json
cd /code && python manage.py collectmedia --noinput
exec "$@"
