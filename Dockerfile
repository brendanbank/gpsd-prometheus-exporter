FROM debian:trixie-slim AS gpsdeps
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-gps \
  && rm -rf /var/lib/apt/lists/*

FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive
# Copy the Debian-packaged gpsd Python module (v3.25 on Trixie) into Python 3.12 site-packages
COPY --from=gpsdeps /usr/lib/python3/dist-packages/gps /usr/local/lib/python3.12/site-packages/gps

# Python deps from PyPI
RUN pip install --no-cache-dir prometheus-client

WORKDIR /app

COPY . /app

ENV GEOPOINT_LON=38.897809878104574
ENV GEOPOINT_LAT=-77.03655125936501

CMD [ "./entrypoint.sh" ]

