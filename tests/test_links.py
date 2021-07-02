import re
from pathlib import Path

import docutils.nodes
from sphinx.application import Sphinx

from sphinx_hyperhelp import HelpTopic
from sphinx_hyperhelp.help_writer import TopicRef

from . import utils
from .utils import build_file, build_file_and_doctree


def test_links(app):
    # copied from Sphinx source code: sphinx/tests/roots/test-linkcheck/links.txt
    w3_url = "https://www.w3.org/TR/2006/REC-xml-names-20060816/#defaulting"
    conf_url = "conf.py"
    rst_file = f"""
* If there is a `default namespace <{w3_url}>`__, that full URI gets prepended to all of the non-prefixed tags.

* `Example valid local file <{conf_url}>`_

.. image:: https://www.duckduckgo.com/image.png

* Monkey D. Luffy <monkey.d.luffy@one.piece>
"""
    help_file, help_index = build_file(app, rst_file)

    assert "default namespace" in help_file
    urls = set(help_index["externals"].keys())
    assert urls == {w3_url}
    # TODO: local file: conf_url
    # TODO: image "https://www.duckduckgo.com/image.png",
    w3_topic = help_index["externals"][w3_url][1]["topic"]
    assert w3_topic == "www.w3.org/TR/2006/REC-xml-names-20060816/#defaulting"
    assert f"|:{w3_topic}:default namespace|" in help_file

    # Hyperhelp doesn't support "mailto" targets
    assert "mailto:" not in help_file
    assert "* Monkey D. Luffy <monkey.d.luffy@one.piece>" in help_file


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


def test_wrap_preserve_links(app):
    rst_file = f"""

.. _examples-documentation-using-the-alabaster-theme:

Documentation using the alabaster theme
--------------------------

* Projects using Sphinx

  * xxx :ref:`examples-documentation-using-the-alabaster-theme`
"""
    help_file, _ = build_file(app, rst_file)
    assert f"  * xxx {ALABSTER_THEME}" in help_file


def test_wrap_short_lines(app):
    rst_file = f"""
this
should
all be
on the same line
.
"""
    help_file, _ = build_file(app, rst_file)
    assert "this should all be on the same line ." in help_file


def test_todo(app):
    rst_file = """hello
    .. todo:: Populate when the 'builders' document is split up."""
    help_file, _ = build_file(app, rst_file)
    assert "Populate when the 'builders' document is split up." not in help_file


def test_uri2topic(app):
    # TODO: the most important things to check is that topic generated when
    # reading the title and when reading the reference are consistent
    rst_file = """.. _dev-deprecated-apis:

Deprecated APIs
===============

:ref:`lot of deprecated apis <dev-deprecated-apis>`
    """
    _, help_index, doctree, translator = build_file_and_doctree(app, rst_file)

    translator.visit_document(doctree)
    title = doctree[1][0]
    assert isinstance(title, docutils.nodes.title)
    topic_from_title = translator.add_title_as_topic(title)

    ref = doctree[1][1][0]
    assert isinstance(ref, docutils.nodes.reference)
    topic_from_ref = translator.uri2topic(ref)

    assert topic_from_title and topic_from_ref

    index_topics = help_index["help_files"]["index.txt"][1:]
    topic_from_index = HelpTopic.from_json(
        utils.unique(lambda x: x["topic"] == "deprecated-apis", index_topics)
    )

    assert topic_from_title in topic_from_index
    assert topic_from_ref in topic_from_index


def test_topic_title(app):

    rst_file = """.. _dev-deprecated-apis:

Deprecated APIs
===============

On developing Sphinx, we are always careful to the compatibility of our APIs.
"""

    _, help_index = build_file(app, rst_file)
    topics = help_index["help_files"]["index.txt"][1:]

    assert len(topics) == 1
    topic_from_index = HelpTopic.from_json(topics[0])
    assert "dev-deprecated-apis" in topic_from_index
    assert topic_from_index.caption == "Deprecated APIs"


def test_docref(app):
    (Path(app.srcdir) / "templating.rst").write_text("Moar templates\n--------------")
    rst_file = """
Templating
----------

The :doc:`guide to templating </templating>` is helpful if you want to write your
"""
    help_file, _ = build_file(app, rst_file)

    assert "|:templating.txt:guide to templating|" in help_file


def test_local_toc(app):
    rst_file = """
=================
Installing Sphinx
=================

.. contents::
   :depth: 1
   :local:
   :backlinks: none

.. highlight:: console

Overview
--------

Linux
-----

Windows
-------
"""
    help_file, _ = build_file(app, rst_file)
    assert "* |:overview:Overview|" in help_file
    assert "* |:linux:Linux|" in help_file


def test_anchor_without_title(app):
    rst_file = """
Heading
=======

.. _anchor-without-title:

On developing Sphinx, we are always careful to the compatibility of our APIs.
"""
    _, help_index = build_file(app, rst_file)
    topics = help_index["help_files"]["index.txt"][1:]

    assert len(topics) == 2
    topic_from_index = HelpTopic.from_json(topics[-1])
    assert "anchor-without-title" == topic_from_index.topic


def test_anchor_in_paragraph(app):
    rst_file = """
Configuration
=============

The Japanese support has these options:

:type:
  _`type` is dotted module path string to specify Splitter implementation

html_search_options for Japanese is re-organized and any custom splitter
can be used by `type`_ settings.
"""
    _, help_index, doctree, translator = build_file_and_doctree(app, rst_file)
    topics = help_index["help_files"]["index.txt"][1:]
    assert len(topics) == 2
    assert topics[0]["topic"] == "configuration"
    assert topics[1]["topic"] == "type"
