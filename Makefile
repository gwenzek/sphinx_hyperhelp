TARGET_NAME=Sphinx
TARGET_REPO=https://github.com/sphinx-doc/sphinx.git
TARGET_VERSION=v4.0.2
ST_PACKAGES=$(HOME)/Library/Application Support/Sublime Text/Packages/

all: test build

# Commands for people wanting to build documentation
# Usage:
# make \
  TARGET_NAME=sphinx \
  TARGET_REPO=https://github.com/sphinx-doc/sphinx.git \
  TARGET_VERSION=v4.0.2

build: build/$(TARGET_NAME)/hyperhelp

build/$(TARGET_NAME)/hyperhelp: repos/$(TARGET_NAME)
	[ ! -f $@/unresolved.txt ] || mv -f $@/unresolved.txt $@/unresolved_prev.txt
	poetry run python -m sphinx -P -b hyperhelp $</doc $(@)
	# DEBUG: Changes in unresolved links:
	diff $@/unresolved.txt $@/unresolved_prev.txt | head

	# Adding $(TARGET_NAME) to ST Packages.
	if [ -h "$(ST_PACKAGES)/$(TARGET_NAME)" ]; then\
		[[ `realpath $(@D)` = `realpath "$(ST_PACKAGES)/$(TARGET_NAME)"` ]] || \
		echo "!!! $(ST_PACKAGES)/$(TARGET_NAME) already exists !!!" ; \
	else \
		ln -sih `realpath $(@D)` "$(ST_PACKAGES)/$(TARGET_NAME)"; \
	fi;

	subl --command 'hyperhelp_topic {"package": "$(TARGET_NAME)", "topic": "contents.txt"}'

build_html: build/$(TARGET_NAME)/html

build/$(TARGET_NAME)/html: repos/$(TARGET_NAME)
	python -m sphinx -P -b html $</doc $@


repos/$(TARGET_NAME):
	git clone --depth 2 --branch $(TARGET_VERSION) $(TARGET_REPO) $@

clean:
	rm -r build/$(TARGET_NAME)
	rm "$(ST_PACKAGES)/$(TARGET_NAME)"


# Command for developers working on sphinx_hyperhelp

install:
	pip install poetry
	poetry install

format:
	poetry run isort .
	poetry run black .

lint:
	poetry run mypy

test:
	poetry run pytest

ci: install format lint test

todo:
	grep 'TODO' README.md sphinx_hyperhelp/*.py
