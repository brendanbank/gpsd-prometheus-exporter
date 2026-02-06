# Makefile for building and copying gpsd Python library
GPSD_REPO = https://gitlab.com/gpsd/gpsd.git
GPSD_VERSION = 3.26.1
GPSD_TEMP_DIR = /tmp/gpsd
GPSD_INSTALL_DIR = /tmp/gpsd-install
TARGET_DIR = ./gps

.PHONY: help clean build-gpsd copy-gpsd all

help: ## Show this help message
	@echo "Available targets:"
	@echo "  build-gpsd    - Clone gpsd repo, build and install Python library only"
	@echo "  copy-gpsd     - Copy installed Python library to ./gps directory"
	@echo "  all           - Build, install and copy gpsd Python library"
	@echo "  clean         - Remove temporary gpsd directory"
	@echo "  help          - Show this help message"

all: build-gpsd copy-gpsd ## Build, install and copy gpsd Python library

build-gpsd: ## Clone gpsd repo, build and install Python library only
	@echo "Cloning gpsd repository..."
	rm -rf $(GPSD_TEMP_DIR)
	git clone $(GPSD_REPO) $(GPSD_TEMP_DIR)
	cd $(GPSD_TEMP_DIR) && git checkout -q release-$(GPSD_VERSION)
	@echo "Building and installing Python library only..."
	cd $(GPSD_TEMP_DIR) && scons install python=yes gpsd=no gpsdclients=no xgps=no libgpsmm=no qt=no shared=yes prefix=$(GPSD_INSTALL_DIR) python_libdir=$(GPSD_INSTALL_DIR)/lib
	@echo "Build and install completed successfully!"

copy-gpsd: ## Copy installed Python library to ./gps directory
	@echo "Copying Python library to $(TARGET_DIR)..."
	rm -rf $(TARGET_DIR)
	cp -r $(GPSD_INSTALL_DIR)/lib/gps $(TARGET_DIR)
	@echo "Copying GPSD license files..."
	cp $(GPSD_TEMP_DIR)/COPYING $(TARGET_DIR)/COPYING
	@echo "Copy completed successfully!"

clean: ## Remove temporary gpsd directory
	@echo "Cleaning up temporary files..."
	rm -rf $(GPSD_TEMP_DIR) $(GPSD_INSTALL_DIR)
	@echo "Cleanup completed!"
