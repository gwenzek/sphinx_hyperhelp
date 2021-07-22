from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock

import pytest
import sphinx.testing.util
from sphinx.application import Sphinx
from sphinx.testing.path import path as SphinxPath

from sphinx_hyperhelp import HyperHelpTranslator


@pytest.fixture()
def app(monkeypatch, tmp_path: Path) -> Iterator[Sphinx]:
    """Creates a SphinxApp, ready to build the `tmp_path` directory.

    This is a simplified version of `shpinx.testing.fixtures.make_app`
    """
    monkeypatch.setattr("sphinx.application.abspath", lambda x: x)
    syspath = sys.path[:]

    conf_file = tmp_path / "conf.py"
    if not conf_file.exists():
        conf_file.write_text("")
    app = sphinx.testing.util.SphinxTestApp(
        "hyperhelp",
        srcdir=SphinxPath(tmp_path),
        # Disable pruning topic, to not force us to reference all topics in tests.
        # pruning is tested in test_hyperhelp.py
        confoverrides={"hyperhelp_prune_topics": False},
    )
    try:
        yield app
    finally:
        app.cleanup()
        sys.path[:] = syspath


@pytest.fixture()
def hh_translator(app: Sphinx) -> HyperHelpTranslator:
    """Return an HyperHelp translator.

    Most of the time this will crash because the translator
    assumes it's working with a builder on a specific document.
    `build_file_and_doctree(app, rst_file)` will return the translator used.
    """
    return HyperHelpTranslator(document=MagicMock(), builder=app.builder)  # type: ignore
