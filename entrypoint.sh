#!/bin/sh

EXPORTER_ARGS=""

[[ -z "${GPSD_HOST}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --hostname ${GPSD_HOST}"
[[ -z "${GPSD_PORT}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --port ${GPSD_PORT}"
[[ -z "${EXPORTER_PORT}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --exporter-port ${EXPORTER_PORT}"

[[ -z "${GEOPOINT_LON}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --geopoint-lon ${GEOPOINT_LON}"
[[ -z "${GEOPOINT_LAT}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --geopoint-lat ${GEOPOINT_LAT}"

./gpsd_exporter.py -v --pps-histogram --offset-from-geopoint $EXPORTER_ARGS

