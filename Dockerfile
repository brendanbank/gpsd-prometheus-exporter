FROM python:alpine3.10

RUN pip install prometheus_client
RUN pip install gps

WORKDIR /app

COPY . /app

ENV GEOPOINT_LON=38.897809878104574
ENV GEOPOINT_LAT=-77.03655125936501


CMD [ "./entrypoint.sh" ]

