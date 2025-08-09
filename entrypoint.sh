#!/bin/sh

EXPORTER_ARGS=""

if [ "${DEBUG}" != "0" ] && [ -n "${DEBUG}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} -d"
fi

# Add verbose flag if VERBOSE is set
if [ -n "${VERBOSE}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} -v"
fi

if [ -n "${GPSD_HOST}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --hostname ${GPSD_HOST}"
fi
if [ -n "${GPSD_PORT}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --port ${GPSD_PORT}"
fi
if [ -n "${EXPORTER_PORT}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --exporter-port ${EXPORTER_PORT}"
fi

if [ -n "${GEOPOINT_LON}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --geopoint-lon ${GEOPOINT_LON}"
fi
if [ -n "${GEOPOINT_LAT}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --geopoint-lat ${GEOPOINT_LAT}"
fi

if [ -n "${GEO_BUCKET_SIZE}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --geo-bucket-size ${GEO_BUCKET_SIZE}"
fi
if [ -n "${GEO_BUCKET_COUNT}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --geo-bucket-count ${GEO_BUCKET_COUNT}"
fi

if [ -n "${PPS_BUCKET_SIZE}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --pps-bucket-size ${PPS_BUCKET_SIZE}"
fi
if [ -n "${PPS_BUCKET_COUNT}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --pps-bucket-count ${PPS_BUCKET_COUNT}"
fi

# Add PPS histogram support if PPS_TIME1 is set
if [ -n "${PPS_TIME1}" ]; then
  EXPORTER_ARGS="${EXPORTER_ARGS} --pps-histogram --pps-time1 ${PPS_TIME1}"
fi

echo ./gpsd_exporter.py --offset-from-geopoint ${EXPORTER_ARGS}
./gpsd_exporter.py --offset-from-geopoint ${EXPORTER_ARGS}

