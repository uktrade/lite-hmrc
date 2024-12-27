FROM python:3.9.18-slim

ENV DOCKERIZE_VERSION v0.6.1

RUN apt update --fix-missing  \
    && apt install libpq-dev gcc wget -y  \
    && apt install build-essential -y --no-install-recommends

RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

WORKDIR /app

ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/bin:$PATH

RUN pip3 install pipenv
ADD Pipfile* /app/
RUN pipenv install --dev --deploy

ADD . /app
