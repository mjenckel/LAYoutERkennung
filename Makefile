testdir = tests

export

CUDA_VISIBLE_DEVICES=0
SHELL = /bin/bash
PYTHON = python
PIP = pip
PIP_INSTALL = $(PIP) install
LOG_LEVEL = INFO
PYTHONIOENCODING=utf8

TESTDATA = $(testdir)/assets/dfki-testdata/data

TESTS=tests

# Tag to publish docker image to
DOCKER_TAG = ocrd/anybaseocr

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    deps                                  Install python deps via pip"
	@echo "    install                               Install"
	@echo "    patch-pix2pixhd                       Patch pix2pixhd to trick it into thinking it was part of this mess"
	@echo "    repo/assets                           Clone OCR-D/assets to ./repo/assets"
	@echo "    assets-clean                          Remove assets"
	@echo "    assets                                Setup test assets"
	@echo "    test                                  Run unit tests"
	@echo "    cli-test                              Run CLI tests"
	@echo "    test-binarize                         Test binarization CLI"
	@echo "    test-deskew                           Test deskewing CLI"
	@echo "    test-crop                             Test cropping CLI"
	@echo "    test-tiseg                            Test text/non-text segmentation CLI"
	@echo "    test-block-segmentation               Test block segmentation CLI"
	@echo "    test-textline                         Test textline extraction CLI"
	@echo "    test-layout-analysis                  Test document structure analysis CLI"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    DOCKER_TAG  Tag to publish docker image to"

# END-EVAL

# Install python deps via pip
deps:
	$(PIP_INSTALL) -r requirements.txt

# Install
install: patch-pix2pixhd
	$(PIP_INSTALL) .
.PHONY: patch-pix2pixhd

# Patch pix2pixhd to trick it into thinking it was part of this mess
PIX2PIX_FILES = ocrd_anybaseocr/pix2pixhd/*/*.py ocrd_anybaseocr/pix2pixhd/*.py
patch-pix2pixhd: pix2pixhd
	touch ocrd_anybaseocr/pix2pixhd/__init__.py
	sed -i 's,^from util,from ..util,' $(PIX2PIX_FILES)
	sed -i 's,^import util,import ..util,' $(PIX2PIX_FILES)
	sed -i 's,^\(\s*\)from data,\1from .data,' ocrd_anybaseocr/pix2pixhd/*.py
	sed -i 's,^\(\s*\)from data,\1from ..data,' ocrd_anybaseocr/pix2pixhd/*/*.py
	# string exceptions, srsly y
	sed -i "s,raise('\([^']*\)',raise(Exception('\1')," $(PIX2PIX_FILES)

pix2pixhd:
	git submodule update --init

#
# Assets
#


# Download sample model TODO Add other models here
.PHONY: models
models:
	ocrd resmgr download --allow-uninstalled --location cwd ocrd-anybaseocr-dewarp '*'
	ocrd resmgr download --allow-uninstalled --location cwd ocrd-anybaseocr-block-segmentation '*'
	ocrd resmgr download --allow-uninstalled --location cwd ocrd-anybaseocr-layout-analysis '*'
	ocrd resmgr download --allow-uninstalled --location cwd ocrd-anybaseocr-tiseg '*'

docker:
	docker build -t '$(DOCKER_TAG)' .

# Clone OCR-D/assets to ./repo/assets
repo/assets:
	mkdir -p $(dir $@)
	git clone https://github.com/OCR-D/assets "$@"

# Remove assets
assets-clean:
	rm -rf $(testdir)/assets

# Setup test assets
assets: repo/assets
	mkdir -p $(testdir)/assets
	cp -r -t $(testdir)/assets repo/assets/data/*
	$(MAKE) models
	ln -sr ocrd-resources/* $(TESTDATA)/
#
# Tests
#

# Run unit tests
test: assets-clean assets
	$(PYTHON) -m pytest --continue-on-collection-errors $(TESTS)

# Run CLI tests
cli-test: assets-clean assets \
	test-binarize test-deskew test-crop test-tiseg test-textline test-layout-analysis

# Test binarization CLI
test-binarize:
	ocrd-anybaseocr-binarize -m $(TESTDATA)/mets.xml -I MAX -O BIN-TEST

# Test deskewing CLI
test-deskew:
	ocrd-anybaseocr-deskew -m $(TESTDATA)/mets.xml -I BIN-TEST -O DESKEW-TEST

# Test cropping CLI
test-crop:
	ocrd-anybaseocr-crop -m $(TESTDATA)/mets.xml -I DESKEW-TEST -O CROP-TEST

# Test text/non-text segmentation CLI
test-tiseg:
	ocrd-anybaseocr-tiseg -m $(TESTDATA)/mets.xml --overwrite -I CROP-TEST -O TISEG-TEST

# Test block segmentation CLI
test-block-segmentation:
	ocrd-anybaseocr-block-segmentation -m $(TESTDATA)/mets.xml -I TISEG-TEST -O OCR-D-BLOCK-SEGMENT

# Test textline extraction CLI
test-textline:
	ocrd-anybaseocr-textline -m $(TESTDATA)/mets.xml -I TISEG-TEST -O TL-TEST

# Test document structure analysis CLI
test-layout-analysis:
	ocrd-anybaseocr-layout-analysis -m $(TESTDATA)/mets.xml -I BIN-TEST -O LAYOUT
