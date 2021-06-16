from __future__ import annotations

from sphinx.application import Sphinx

from .utils import build_file


def test_directives(app: Sphinx):
    rst_file = """
The reStructuredText domain
---------------------------

The reStructuredText domain (name **rst**) provides the following directives:

.. rst:directive:: .. rst:directive:: name

   Describes a reST directive.  The *name* can be a single directive name or
   actual directive syntax (`..` prefix and `::` suffix) with arguments that
   will be rendered differently.  For example::

      .. rst:directive:: foo

         Foo description.

      .. rst:directive:: .. bar:: baz

         Bar description.

   will be rendered as:

      .. rst:directive:: foo

         Foo description.

      .. rst:directive:: .. bar:: baz

         Bar description.
   """

    help_file, help_index = build_file(app, rst_file)
    topics: list[dict] = help_index["help_files"]["index.txt"][1:]
    assert find_topic("directive-rst-directive", topics)
    assert find_topic("index.txt/directive-rst-directive", topics)

    print(help_file)
    assert "```rst\n.. rst:directive:: foo\n" in help_file
    assert "\n   Bar description.\n```\n" in help_file


def find_topic(name: str, topics: list[dict]) -> dict:
    for topic in topics:
        if name == topic["topic"] or name in topic["aliases"]:
            return topic
    return {}
