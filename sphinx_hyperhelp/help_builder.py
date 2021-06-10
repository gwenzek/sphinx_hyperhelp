from pathlib import Path
from typing import Any, Dict, Iterator, Set, Tuple

from docutils.io import StringOutput
from docutils.nodes import Node

from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.osutil import ensuredir, os_path
from sphinx.builders.text import TextBuilder
from .help_writer import HyperHelpTranslator, HyperHelpWriter
from .hyperhelp import HelpFile, HelpIndex


logger = logging.getLogger(__name__)


class HyperHelpBuilder(TextBuilder):
    name = "hyperhelp"
    format = "hyperhelp"
    epilog = __("The hyperhelp files are in %(outdir)s, index at %(outdir)s/hyperhelp.json")

    out_suffix = ".txt"
    allow_parallel = True
    default_translator_class = HyperHelpTranslator

    current_docname: str = ""
    index: HelpIndex = None  # type: ignore

    def prepare_writing(self, docnames):
        self.writer = HyperHelpWriter(self)
        config = self.config
        description = config.epub_description or config.html_title
        # print(
        #     {k: v[0] for k, v in config.values.items() if not callable(v[0]) and v[0]}
        # )
        self.index = HelpIndex(config.project, description, Path(self.outdir))

    # TODO: edit reload existing index, and override get_outdated_docs
    # to keep unchanged files in the index
    def get_outdated_docs(self) -> Iterator[str]:
        yield from []

    def finish(self) -> None:
        self.index.save()

    def add_help_file(self) -> HelpFile:
        docname = self.current_docname
        assert docname
        # breakpoint()
        help_file = HelpFile(docname)

        self.index.help_files[help_file.module + ".txt"] = help_file
        return help_file


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_builder(HyperHelpBuilder)

    # app.add_config_value("text_sectionchars", '*=-~"+`', "env")
    # app.add_config_value("text_newlines", "unix", "env")
    # app.add_config_value("text_add_secnumbers", True, "env")
    # app.add_config_value("text_secnumber_suffix", ". ", "env")

    return {
        "version": "builtin",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
