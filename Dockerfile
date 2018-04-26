FROM python:3
ADD . /code
WORKDIR /code
RUN apt-get update -y
RUN pip install --upgrade pip
RUN apt-get -y install postgresql libpq-dev postgresql-client postgresql-client-common libncurses5-dev git
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/Supervisor/supervisor
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
