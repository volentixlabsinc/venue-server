FROM python:3.6-alpine3.8
RUN pip install --upgrade pip && \
    apk --no-cache -U add gcc build-base linux-headers  \
    postgresql-dev ncurses-dev git gettext libffi-dev libressl-dev mailcap && \
    pip install git+https://github.com/Supervisor/supervisor.git@363283c71ed11054bdd8756b78e7777f160dcf05 && \
    apk del git

COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt && \
    pip uninstall -y pycrypto && \
    pip install pycryptodome==3.6.6

ADD . /code
WORKDIR /code

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN python manage.py compilemessages
