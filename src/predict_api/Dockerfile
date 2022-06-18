FROM python:3.8.12-alpine3.15

# Ensure terminal output is sent directly to logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# uvicorn/uvloop/pymssql and other requirements
RUN apk add gcc g++ musl-dev python3-dev libffi-dev openssl-dev make freetds-dev

# Install requirements
# TODO: separate development from production requirements (and Dockerfiles)
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

ADD ../model /model

WORKDIR /app
