FROM python:3.8.12-alpine3.15

# TODO: configure pre-requistes for uvicorn/uvloop
# RUN apk add gcc g++ musl-dev python3-dev libffi-dev openssl-dev make freetds-dev

# Ensure terminal output is sent directly to logs
ENV PYTHONBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH=/app

# Install requirements
# TODO: separate development from production requirements (and Dockerfiles)
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

WORKDIR /app
