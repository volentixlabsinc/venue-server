FROM python:3
RUN apt-get update -y
RUN pip install --upgrade pip
RUN apt-get -y install postgresql libpq-dev postgresql-client postgresql-client-common libncurses5-dev git
COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/Supervisor/Supervisor
ADD . /code
WORKDIR /code
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
