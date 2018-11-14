# FROM python:3.7-alpine3.7
FROM resin/raspberry-pi-alpine-python:latest

ENV WORKDIR /usr/src/rc433mq
RUN mkdir -p ${WORKDIR}

COPY . ${WORKDIR}

RUN apk add --update --no-cache \
    build-base \
    python3 \
    python3-dev \
    bash

RUN pip3 install -U pip
RUN pip3 install -r ${WORKDIR}/requirements.txt

ENV PYTHONPATH=${WORKDIR}

CMD [ "python3", "/usr/src/rc433mq/consume.py" ]