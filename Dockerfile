FROM python:3.6
RUN apt-get update -y && \
    pip install --upgrade pip && \
    apt-get -y install libpq-dev libncurses5-dev git gettext --no-install-recommends && \
    pip install git+https://github.com/Supervisor/supervisor.git@363283c71ed11054bdd8756b78e7777f160dcf05 && \
    apt-get remove git -y && apt-get autoremove -y && apt-get autoclean -y
COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

ADD . /code
WORKDIR /code

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
