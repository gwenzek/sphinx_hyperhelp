TARGET_NAME=Sphinx
TARGET_REPO=https://github.com/sphinx-doc/sphinx.git
TARGET_VERSION=v4.0.2
ST_PACKAGES=$(HOME)/Library/Application Support/Sublime Text/Packages/

FMT_FLAGS=
ifeq ($(CI), true)
	FMT_FLAGS=--check --diff
endif

all: test build

# Commands for people wanting to build documentation
# Usage:
# make \
  TARGET_NAME=sphinx \
  TARGET_REPO=https://github.com/sphinx-doc/sphinx.git \
  TARGET_VERSION=v4.0.2

build: build/$(TARGET_NAME)/hyperhelp

build/$(TARGET_NAME)/hyperhelp:
	poetry run sphinx_hyperhelp --name $(TARGET_NAME) --repo $(TARGET_REPO) --tag $(TARGET_VERSION)

build_html: build/$(TARGET_NAME)/html

build/$(TARGET_NAME)/html: repos/$(TARGET_NAME)
	poetry run python -m sphinx -P -b html $</doc $@

repos/$(TARGET_NAME):
	git clone --depth 2 --branch $(TARGET_VERSION) $(TARGET_REPO) $@

clean:
	rm -r build/$(TARGET_NAME)
	[[ ! -f "$(ST_PACKAGES)/$(TARGET_NAME)" ]] || rm "$(ST_PACKAGES)/$(TARGET_NAME)"


# Command for developers working on sphinx_hyperhelp

install:
	pip install poetry
	poetry install

format:
	poetry run isort $(FMT_FLAGS) .; poetry run black $(FMT_FLAGS) .

lint:
	poetry run mypy

test:
	poetry run pytest

ci: install format lint test

todo:
	grep 'TODO' README.md sphinx_hyperhelp/*.py
