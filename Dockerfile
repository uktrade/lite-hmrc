FROM python:3.8.17-slim

WORKDIR /app

RUN apt update --fix-missing  \
    && apt install libpq-dev gcc -y  \
    && apt install build-essential -y --no-install-recommends

ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/bin:$PATH

RUN pip3 install pipenv
ADD Pipfile* /app/
RUN pipenv install --dev --deploy


ADD . /app
