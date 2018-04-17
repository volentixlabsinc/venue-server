#!/bin/bash
cd /code && python manage.py collectstatic --noinput
cd /code && python manage.py migrate
cd /code && echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'default2018')" | python manage.py shell
cd /code && python manage.py loaddata venue/fixtures/forumsite.json
cd /code && python manage.py loaddata venue/fixtures/forumuserrank.json
cd /code && python manage.py loaddata venue/fixtures/language.json
cd /code && python manage.py loaddata venue/fixtures/notification.json
cd /code && python manage.py loaddata venue/fixtures/signature.json
supervisord -c /code/supervisord.conf
exec "$@"
