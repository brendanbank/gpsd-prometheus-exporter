----------------------------------------
## What's New in 1.0.2

### Changes since commit a395c6ffe5d6383d6c6d58e4b77c8c803f366180

- e18b986 Refactor GitHub Actions workflow for Docker publishing: remove Trivy security scan job and add support for multiple platforms in the build process.
- 9b2cb45 fix CI/CD workflows
- 0b4f5f4 Update docker-compose.yml to add new environment variables for PPS_TIME1, DEBUG, and VERBOSE, enhancing configuration options for the service.
- 676ec42 Enhance GitHub Actions workflow for Docker publishing by adding Docker Buildx setup and building an image for Trivy vulnerability scanning. Update Trivy scan configuration to use the newly built image and skip version checks.
- ee639ec Update GitHub Actions workflow for Docker publishing: add exit code and severity filters for Trivy scan, and upgrade upload action to v3.
- 7e9d2bf Update README.md to add a closing note wishing users good luck. Test CI/CD
- 70f9be3 auto release notes
- 20b1dc3 dd github actions.
- f827bce Update PUBLISHING.md to remove unnecessary package permissions, add section on enabling package publishing, and include troubleshooting tips for repository settings.
- d2d02b9 Refactor gpsd_exporter.py to use the packaging module for gps version checks, enhancing compatibility and error handling. Add a new PUBLISHING.md file detailing the process for publishing the Docker image to GitHub Container Registry, including CI/CD pipeline features and best practices.
- 1c833b9 Update gpsd_exporter.py to increase default retry delay from 5 to 10 seconds, improve error handling for connection issues, and adjust README.md to clarify gps version requirements, now specifying a minimum of 3.18.
- 915512c raise kb error
- 0e1cdf1 Update Dockerfile to use Python 3.12 for improved compatibility and performance.
- 79e067c Update Dockerfile to install the latest gps package version. Modify gpsd_exporter.py to handle JSON encoding issues in newer Python versions and adjust version constraints for the gps package. Update README.md to reflect the new gps version requirement.
- 3b6d067 Refactor error handling in gpsd_exporter.py to re-raise KeyboardInterrupt for proper shutdown management in the main loop.
- 43a1ba9 Update docker-compose.yml to use specific GitHub username for image. Modify Dockerfile to install gps version 3.25 for compatibility. Enhance gpsd_exporter.py to enforce gps version constraints. Update README.md to reflect the requirement for gps version 3.25.
- 01a69c6 Enhance docker-compose and entrypoint scripts to support new environment variables for verbose output and PPS histogram. Updated README.md to reflect changes in environment variable configuration and added details on enhanced features for local builds.
- f878f1e Update docker-compose.build.yml to set default value for DEBUG variable
- e00de2f Update entrypoint.sh to refine DEBUG variable handling for exporter arguments
- 1937923 docker build with local connections to gpds
- cf22890 Enhance gpsd_exporter.py with connection timeout and retry logic. Updated docker-compose.build.yml to include DEBUG environment variable and set network mode to host.
- d585e85 create a seperate docker-compose file to biuld the image locally.
- 791514a Refactor docker-compose.yml to use environment variables for configuration. Updated README.md to include instructions for creating a .env file and using environment variables with docker-compose.
- 710d79c Enhanced error handling in gpsd_exporter.py to manage missing satellite data and connection issues. Added try-except blocks in key functions to log warnings and errors without crashing the application.

### Docker Image

The Docker image is available at:
```bash
ghcr.io/brendanbank/gpsd-prometheus-exporter:1.0.2
```

### Usage

```bash
docker run -d \
  --name gpsd-exporter \
  -p 9015:9015 \
  -e GPSD_HOST=host.docker.internal \
  ghcr.io/brendanbank/gpsd-prometheus-exporter:1.0.2
```

### Multi-Platform Support

This release includes Docker images for:
- **linux/amd64**: Intel/AMD 64-bit processors
- **linux/arm64/v8**: Apple Silicon, modern ARM64 servers
- **linux/arm/v7**: Raspberry Pi, older ARM devices

Docker will automatically select the correct image for your platform.