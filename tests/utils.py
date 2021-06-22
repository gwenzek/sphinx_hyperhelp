from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, TypeVar

import docutils.nodes
from sphinx.application import Sphinx

from sphinx_hyperhelp import HyperHelpTranslator

T_co = TypeVar("T_co", covariant=True)


def build_file(app: Sphinx, content: str) -> tuple[str, dict]:
    """Converts one .rst file to hyperhelp. Also returns the hyperhelp.json file."""

    (Path(app.srcdir) / "index.rst").write_text(content)
    app.build()
    outdir = Path(app.outdir)
    json_index = json.loads((outdir / "hyperhelp.json").read_text())
    help_file = (outdir / "index.txt").read_text()
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
    doctree = app.builder._doctree  # type: ignore
    assert isinstance(doctree, docutils.nodes.document)
    translator = app.builder._translator  # type: ignore
    assert isinstance(translator, HyperHelpTranslator)
    return help_file, json_index, doctree, translator


def unique(condition: Callable[[T_co], bool], elements: list[T_co]) -> T_co:
    matching = [x for x in elements if condition(x)]
    assert len(matching) == 1
    return matching[0]
