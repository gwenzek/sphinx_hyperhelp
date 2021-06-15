import re
from pathlib import Path

import docutils.nodes

from sphinx_hyperhelp import HelpTopic
from sphinx_hyperhelp.help_writer import TopicRef


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


ALABSTER_THEME = (
    "|:examples-documentation-using-the-alabaster-theme"
    ":Documentation using the alabaster theme|"
)


def test_split_preserve_links(hh_translator):
    assert len(TopicRef(ALABSTER_THEME)) == len(
        "|Documentation using the alabaster theme|"
    )
    lines = [
        "If there is a ",
        TopicRef(ALABSTER_THEME),
        ", that full URI gets prepended to all of the non-prefixed tags.",
    ]
    splits = hh_translator.split(lines)

    assert ALABSTER_THEME in splits
    assert splits[:9] == ["If", " ", "there", " ", "is", " ", "a", " ", ALABSTER_THEME]
    assert hh_translator.split(TopicRef(ALABSTER_THEME)) == [ALABSTER_THEME]


def test_wrap_preserve_links(build_file):
    rst_file = f"""

.. _examples-documentation-using-the-alabaster-theme:

Documentation using the alabaster theme
--------------------------

* Projects using Sphinx

  * xxx :ref:`examples-documentation-using-the-alabaster-theme`
"""
    help_file, _ = build_file(rst_file)
    assert f"  * xxx {ALABSTER_THEME}" in help_file


def test_wrap_short_lines(build_file):
    rst_file = f"""
this
should
all be
on the same line
.
"""
    help_file, _ = build_file(rst_file)
    assert "this should all be on the same line ." in help_file


def test_todo(build_file):
    RST_TODO = """hello
    .. todo:: Populate when the 'builders' document is split up."""
    result, _ = build_file(RST_TODO)
    assert "Populate when the 'builders' document is split up." not in result


# def test_uri2topic():
# TODO: the most important things to check is that topic generated when
# reading the title and when reading the reference are consistent

def test_topic_title(build_file):

    rst_file = """.. _dev-deprecated-apis:

Deprecated APIs
===============

On developing Sphinx, we are always careful to the compatibility of our APIs.
"""

    _, help_index = build_file(rst_file)
    topics = help_index["help_files"]["index.txt"][1:]

    assert len(topics) == 1
    assert "dev-deprecated-apis" in HelpTopic.from_json(topics[0])

def test_docref(app, build_file):
    (Path(app.srcdir) / "templating.rst").write_text("Moar templates\n--------------")
    rst_file = """
Templating
----------

The :doc:`guide to templating </templating>` is helpful if you want to write your
"""
    help_file, _ = build_file(rst_file)

    assert "|:templating.txt:guide to templating|" in help_file

