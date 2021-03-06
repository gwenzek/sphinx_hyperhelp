import re

from .utils import build_file


def test_table(app):
    # copied from Sphinx source code: https://github.com/sphinx-doc/sphinx/blob/71e732014ffe5a58a0c52ac16c948ef13d99d19d/sphinx/application.py#L901-L932
    rst_file = """
################
  Sample table
################

Register a Docutils transform to be applied after parsing.

Add the standard docutils :class:`Transform` subclass *transform* to
the list of transforms that are applied after Sphinx parses a reST
document.

:param transform: A transform class

.. list-table:: priority range categories for Sphinx transforms
   :widths: 20,80

   * - Priority
     - Main purpose in Sphinx
   * - 0-99
     - Fix invalid nodes by docutils. Translate a doctree.
   * - 100-299
     - Preparation
   * - 300-399
     - early
   * - 400-699
     - main
   * - 700-799
     - Post processing. Deadline to modify text and referencing.
   * - 800-899
     - Collect referencing and referenced nodes. Domain processing.
   * - 900-999
     - Finalize and clean up.

refs: `Transform Priority Range Categories`__

__ http://docutils.sourceforge.net/docs/ref/transforms.html#transform-priority-range-categories

"""
    help_file, _ = build_file(app, rst_file)
    help_file = re.sub(r" +", " ", help_file)
    assert "| Priority | Main purpose in Sphinx |" in help_file
