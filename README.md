# Sphinx Hyperhelp

[Sphinx](https://www.sphinx-doc.org/en/master/index.html) builder that outputs 
[HyperHelp](https://github.com/STealthy-and-haSTy/hyperhelpcore) files.
HyperHelp files are destined to be read inside [Sublime Text](https://www.sublimetext.com/)
The goal of this project is to be able to read in Sublime Text
the documentation of all projects using Sphinx.
Notably [Python](https://docs.python.org/3/) documentation.

## License

This plugin is released under the [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause).

This plugin is mostly based on the builtin [Sphinx text builder](https://www.sphinx-doc.org/en/master/usage/builders/index.html?highlight=text%20builder#sphinx.builders.text.TextBuilder).

Some of the code is only a slight modification of Sphinx.
[Sphinx license](./LICENSE#17)


## Get started

* Install this repository: `pip install sphinx_hyperhelp`

* Run `sphinx_hyperhelp --help` for help

* Run `sphinx_hyperhelp --name Sphinx --repo https://github.com/sphinx-doc/sphinx.git`
  If it succeeds it will open the Sphinx documentation inside Sublime Text

* You can also use the `sphinx` command line itself
and chose `hyperhelp` as the output format.
You'll need to move yourself the generated folder to ST Packages folder.


## How-to ?

### How to install for developement

Sphinx hyperhelp uses [Poetry](https://python-poetry.org/) as Python package manager

```sh
git clone git@github.com:gwenzek/sphinx_hyperhelp.git
cd sphinx_hyperhelp

pip install poetry
# Note: here poetry will create a virtual env for sphinx_hyperhelp
poetry install
```

Then you're good to go !
* `make test` for running the tests
* `make ci` for full formatting / linting / testing
* `make build` for building the documentation of the Sphinx project itself


## Architecture

This plugin is mostly based on the builtin [Sphinx text builder](https://www.sphinx-doc.org/en/master/usage/builders/index.html?highlight=text%20builder#sphinx.builders.text.TextBuilder).
There are some visual differences so that the generated text looks
nice when parsed by HyperHelp renderer.
But a big part of the work is also to generate the HyperHelp index,
that registers all anchors.

* `hyperhelp.py` files contains helpers to build the index.
* `help_writer.py` is doing the core of the work,
  and is implemented by only overriding
  some of the TextTranslator methods.
* `help_builder.py` is mostly sphinx boilerplate and post-build validation
* `tests` has all the tests, `tests/conftest.py` and `test/utils.py` 
  contains helpers for writing more tests.
  Most of the tests use sample of the actual Sphinx documentation.

Currently this project is made to be compatible by Python 3.8,
but with a `__future__.annotations` to get nicer type hints.


## Reference

...

## Todo list

* fix broken links (currently 132 unresolved topics, 6 ambiguous out of 953 links)
* ensure links are surrounded by spaces
* incremental compilation 
* create a table of contents for HyperHelp, by parsing the `root_doc`

## Crazy ideas

* Use unicode to render maths: "E = mc^2" -> "E = mc²"
* images using phantoms ? this should be an HyperHelp feature
