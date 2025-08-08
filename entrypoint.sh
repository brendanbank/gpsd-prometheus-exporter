#!/bin/sh

EXPORTER_ARGS=""

[[ "${DEBUG}" != "0" && -n "${DEBUG}" ]] && EXPORTER_ARGS="${EXPORTER_ARGS} -d"

# Add verbose flag if VERBOSE is set
[[ -n "${VERBOSE}" ]] && EXPORTER_ARGS="${EXPORTER_ARGS} -v"

[[ -z "${GPSD_HOST}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --hostname ${GPSD_HOST}"
[[ -z "${GPSD_PORT}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --port ${GPSD_PORT}"
[[ -z "${EXPORTER_PORT}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --exporter-port ${EXPORTER_PORT}"

[[ -z "${GEOPOINT_LON}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --geopoint-lon ${GEOPOINT_LON}"
[[ -z "${GEOPOINT_LAT}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --geopoint-lat ${GEOPOINT_LAT}"

[[ -z "${GEO_BUCKET_SIZE}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --geo-bucket-size ${GEO_BUCKET_SIZE}"
[[ -z "${GEO_BUCKET_COUNT}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --geo-bucket-count ${GEO_BUCKET_COUNT}"

[[ -z "${PPS_BUCKET_SIZE}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --pps-bucket-size ${PPS_BUCKET_SIZE}"
[[ -z "${PPS_BUCKET_COUNT}" ]] || EXPORTER_ARGS="${EXPORTER_ARGS} --pps-bucket-count ${PPS_BUCKET_COUNT}"

# Add PPS histogram support if PPS_TIME1 is set
[[ -n "${PPS_TIME1}" ]] && EXPORTER_ARGS="${EXPORTER_ARGS} --pps-histogram --pps-time1 ${PPS_TIME1}"

echo ./gpsd_exporter.py --offset-from-geopoint $EXPORTER_ARGS
./gpsd_exporter.py --offset-from-geopoint $EXPORTER_ARGS

