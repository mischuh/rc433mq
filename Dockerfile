FROM python:3.7-alpine3.7

ENV WORKDIR /usr/src/rc433mq
RUN mkdir -p ${WORKDIR} && \
    cd ${WORKDIR}

COPY . ${WORKDIR}
RUN pip3 install --no-cache-dir -r ${WORKDIR}/requirements.txt

ENV PYTHONPATH=${WORKDIR}

CMD [ "python3", "/usr/src/rc433mq/consume.py" ]