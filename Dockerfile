FROM debian:trixie-slim

# Prevent debconf from trying to use interactive frontends during build
ENV DEBIAN_FRONTEND=noninteractive

# Use distro Python and libraries so python3-gps matches the interpreter
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-gps \
    python3-prometheus-client \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

ENV GEOPOINT_LON=38.897809878104574
ENV GEOPOINT_LAT=-77.03655125936501

CMD [ "./entrypoint.sh" ]

