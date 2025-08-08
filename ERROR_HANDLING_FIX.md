# GPSD Exporter Error Handling Fix

## Issue Description

The GPSD exporter was crashing due to `KeyError: 'az'` when GPSD reported satellite data that didn't include azimuth information. This is a common issue when GPSD reports incomplete satellite data.

## Root Cause

The error occurred in the GPS library's `__getitem__` method when trying to access `sat['az']` (azimuth) from satellite data that didn't contain this field. The GPS library was trying to access satellite data fields that may not be present in all GPSD reports.

## Fixes Applied

### 1. Main Data Processing Loop (`getPositionData` function)

Added comprehensive error handling around the `gpsd.next()` call:

```python
def getPositionData(gpsd, metrics, args):
    try:
        nx = gpsd.next()
    except KeyError as e:
        # Handle missing satellite data fields (like 'az', 'el', etc.)
        log.warning(f"GPSD reported incomplete satellite data: {e}")
        return
    except Exception as e:
        # Handle other GPSD connection or data parsing errors
        log.error(f"Error reading from GPSD: {e}")
        return
```

### 2. Satellite Statistics Processing (`add_sat_stats` function)

Added error handling for individual satellite processing:

```python
def add_sat_stats(satellites):
    for sat in satellites:
        try:
            ts = time.time()
            ts_new = int(ts)
            sat_queue.put({'sat': sat, 'ts': ts})
        except KeyError as e:
            # Handle missing satellite data fields
            log.warning(f"Skipping satellite with missing data field: {e}")
            continue
        except Exception as e:
            # Handle other satellite data processing errors
            log.error(f"Error processing satellite data: {e}")
            continue
```

### 3. Satellite Metrics Collection (`SatCollector.collect` method)

Added error handling for satellite metrics processing:

```python
for sat in last_measurement.keys():
    try:
        for key in metrics.keys():
            sat_dict = last_measurement[sat]
            if key in sat_dict.keys():
                metrics[key].add_metric([str(sat_dict['PRN']), str(sat_dict['svid']), str(sat_dict['gnssid']), str(sat_dict['used'])], sat_dict[key])
    except KeyError as e:
        # Handle missing satellite data fields
        log.warning(f"Skipping satellite metrics due to missing field: {e}")
        continue
    except Exception as e:
        # Handle other satellite metrics processing errors
        log.error(f"Error processing satellite metrics: {e}")
        continue
```

### 4. Main Connection Loop (`loop_connection` function)

Added error handling to prevent container crashes:

```python
running = True
while running:
    try:
        getPositionData(gpsd, metrics, args)
    except KeyboardInterrupt:
        log.info("Received keyboard interrupt, shutting down...")
        running = False
    except Exception as e:
        log.error(f"Unexpected error in main loop: {e}")
        # Continue running to avoid crashing the container
        continue
```

### 5. Satellite Queue Processing

Added error handling for satellite measurement processing:

```python
while not sat_queue.empty():
    try:
        measurement = sat_queue.get()
        sat = measurement['sat']
        ts = measurement['ts']
        last_measurement[sat['PRN']] = sat
    except KeyError as e:
        # Handle missing satellite data fields
        log.warning(f"Skipping satellite measurement due to missing field: {e}")
        continue
    except Exception as e:
        # Handle other satellite measurement processing errors
        log.error(f"Error processing satellite measurement: {e}")
        continue
```

## Benefits

1. **Prevents Container Crashes**: The exporter will no longer crash when GPSD reports incomplete satellite data
2. **Graceful Degradation**: Missing satellite data is logged as warnings but doesn't stop the exporter
3. **Better Logging**: Clear error messages help with debugging and monitoring
4. **Robust Operation**: The exporter continues to function even with incomplete GPS data

## Testing

The error handling has been tested to ensure that:
- Missing satellite data fields are handled gracefully
- The exporter continues running after encountering data errors
- Appropriate warning and error messages are logged
- No data corruption occurs when processing incomplete satellite data

## Compatibility

These changes maintain full backward compatibility with existing GPSD configurations and don't affect the normal operation when complete satellite data is available.
