import json
import sys
from pathlib import Path

import pytest
import sphinx.testing.util
from sphinx.testing.path import path as SphinxPath


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
def file_builder(app):
    """Converts one file"""

    def _builder(content: str) -> str:
        (Path(app.srcdir) / "index.rst").write_text(content)
        app.build()
        return (app.outdir / "index.txt").read_text()

    return _builder


@pytest.fixture()
def load_help_index(tmp_path: Path):
    return lambda: json.loads(
        (tmp_path / "_build/hyperhelp/hyperhelp.json").read_text()
    )
