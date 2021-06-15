from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import sphinx.testing.util
from sphinx.testing.path import path as SphinxPath

from sphinx_hyperhelp import HyperHelpTranslator


@pytest.fixture()
def app(monkeypatch, tmp_path: Path):
    """Creates a SphinxApp, ready to build the `tmp_path` directory.

    This is a simplified version of `shpinx.testing.fixtures.make_app`
    """
    monkeypatch.setattr("sphinx.application.abspath", lambda x: x)
    syspath = sys.path[:]

    conf_file = tmp_path / "conf.py"
    if not conf_file.exists():
        conf_file.write_text("")
    app = sphinx.testing.util.SphinxTestApp("hyperhelp", srcdir=SphinxPath(tmp_path))
    try:
        yield app
    finally:
        app.cleanup()
        sys.path[:] = syspath


@pytest.fixture()
def build_file(app):
    """Converts one file"""

    def _builder(content: str) -> tuple[str, list[dict]]:
        (Path(app.srcdir) / "index.rst").write_text(content)
        app.build()
        json_index = json.loads((app.outdir / "hyperhelp.json").read_text())
        return (app.outdir / "index.txt").read_text(), json_index

    return _builder


@pytest.fixture()
def hh_translator(app) -> HyperHelpTranslator:
    return HyperHelpTranslator(document=MagicMock(), builder=app.builder)
