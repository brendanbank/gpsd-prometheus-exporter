FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app

# Python deps from PyPI
RUN pip install --no-cache-dir prometheus-client

WORKDIR /app

# Copy only required runtime files
COPY entrypoint.sh /app/
COPY gpsd_exporter.py /app/
COPY gps /app/gps

RUN chmod +x /app/entrypoint.sh

ENV GEOPOINT_LON=38.897809878104574
ENV GEOPOINT_LAT=-77.03655125936501

CMD [ "./entrypoint.sh" ]

