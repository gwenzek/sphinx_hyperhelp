import re
from pathlib import Path
from unittest.mock import MagicMock

import docutils.nodes

from sphinx_hyperhelp import HyperHelpBuilder, HyperHelpTranslator


def test_links(build_file):
    # copied from Sphinx source code: sphinx/tests/roots/test-linkcheck/links.txt
    w3_url = "https://www.w3.org/TR/2006/REC-xml-names-20060816/#defaulting"
    conf_url = "conf.py"
    RST_LINKS = f"""
* If there is a `default namespace <{w3_url}>`__, that full URI gets prepended to all of the non-prefixed tags.

* `Example valid local file <{conf_url}>`_

.. image:: https://www.duckduckgo.com/image.png
"""
    result, help_index = build_file(RST_LINKS)

    assert "default namespace" in result
    urls = set(help_index["externals"].keys())
    assert urls == {w3_url, conf_url}
    # "https://www.duckduckgo.com/image.png",
    w3_topic = help_index["externals"][w3_url][1]["topic"]
    assert w3_topic == "www.w3.org/TR/2006/REC-xml-names-20060816/#defaulting"
    assert f"|:{w3_topic}:default namespace|" in result


def test_split_preserve_links(app):
    long_text = (
        "If there is a "
        "|:www.w3.org/TR/2006/REC-xml-names-20060816/#defaulting:default namespace|,"
        " that full URI gets prepended to all of the non-prefixed tags."
    )
    hh_translator = HyperHelpTranslator(document=MagicMock(), builder=app.builder)
    splits = hh_translator.split(long_text)

    assert (
        "|:www.w3.org/TR/2006/REC-xml-names-20060816/#defaulting:default namespace|"
        in splits
    )


# def test_uri2topic():
#     assert (
#         uri2topic(Path("changes"), "#confval-man_make_section_directory")
#         == "confval-man_make_section_directory"
#     )

def test_todo(build_file):
    RST_TODO = """hello
    .. todo:: Populate when the 'builders' document is split up."""
    result, _ = build_file(RST_TODO)
    assert "Populate when the 'builders' document is split up." not in result
