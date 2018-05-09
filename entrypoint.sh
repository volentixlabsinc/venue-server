#!/bin/bash
cd /code && python manage.py collectstatic --noinput
cd /code && python manage.py migrate
cd /code && echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'default2018')" | python manage.py shell
cd /code && python manage.py loaddata venue/fixtures/*.json
exec "$@"
