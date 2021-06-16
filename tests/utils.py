from __future__ import annotations

import json
from pathlib import Path

import docutils.nodes
from sphinx.application import Sphinx

from sphinx_hyperhelp import HyperHelpTranslator


def build_file(app: Sphinx, content: str) -> tuple[str, dict]:
    """Converts one .rst file to hyperhelp. Also returns the hyperhelp.json file."""

    (Path(app.srcdir) / "index.rst").write_text(content)
    app.build()
    json_index = json.loads((app.outdir / "hyperhelp.json").read_text())
    help_file = (app.outdir / "index.txt").read_text()
    return help_file, json_index


def build_file_and_doctree(
    app: Sphinx, content: str
) -> tuple[str, dict, docutils.nodes.document, HyperHelpTranslator]:
    """Converts one .rst file to hyperhelp.

    Also return the index, the parsed doctree and the translator object.
    Note: the translator object is "closed" and some methods might not work.
    We may need to add a factory that creates and prepares a translator.
    """
    help_file, json_index = build_file(app, content)
    doctree = app.builder._doctree
    assert isinstance(doctree, docutils.nodes.document)
    translator = app.builder._translator
    assert isinstance(translator, HyperHelpTranslator)
    return help_file, json_index, doctree, translator
