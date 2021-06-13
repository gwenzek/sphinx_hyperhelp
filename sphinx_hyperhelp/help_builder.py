from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterator, Set, Tuple

from docutils.io import StringOutput
from docutils.nodes import Node
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.builders.text import TextBuilder
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.osutil import ensuredir, os_path

from .help_writer import HyperHelpTranslator, HyperHelpWriter
from .hyperhelp import HelpFile, HelpIndex

logger = logging.getLogger(__name__)


class HyperHelpBuilder(TextBuilder):
    name = "hyperhelp"
    format = "text"
    epilog = __(
        "The hyperhelp files are in %(outdir)s, index at %(outdir)s/hyperhelp.json"
    )

    out_suffix = ".txt"
    allow_parallel = True
    default_translator_class = HyperHelpTranslator

    current_docname: str = ""
    index: HelpIndex = None  # type: ignore
    links: dict[str, str] = {}

    def prepare_writing(self, docnames):
        self.writer = HyperHelpWriter(self)
        config = self.config
        description = config.epub_description or config.html_title
        # print(
        #     {k: v[0] for k, v in config.values.items() if not callable(v[0]) and v[0]}
        # )
        self.index = HelpIndex(config.project, description, Path(self.outdir))
        self.links = {}

    # TODO: edit reload existing index, and override get_outdated_docs
    # to keep unchanged files in the index
    def get_outdated_docs(self) -> Iterator[str]:
        yield from self.env.found_docs

    def get_target_uri(self, docname: str, typ: str = None) -> str:
        return docname

    def get_relative_uri(self, from_: str, to: str, typ: str = None) -> str:
        # ignore source path, Hyperhelp only has absolute paths
        # This is used when generating toctree.
        return self.get_target_uri(to, typ)

    def finish(self) -> None:
        self.index.save()
        valid = self.validate()
        if not valid:
            logger.error("The index seems invalid, some topics may be missing")

    def validate(self) -> bool:
        all_topics = [
            (hf.module, help_topic)
            for hf in self.index.help_files.values()
            for help_topic in hf.topics
        ]
        resolved_topics: dict[str, str] = {}
        conflicts_set: dict[str, set[str]] = defaultdict(set)
        for file, help_topic in all_topics:
            topic = help_topic.topic
            conflict = resolved_topics.get(topic)
            if conflict:
                conflicts_set[topic].add(conflict)
                conflicts_set[topic].add(file)
                continue
            resolved_topics[topic] = file
            for alias in help_topic.aliases:
                resolved_topics[alias] = file

        conflicts = []
        unresolveds = []
        for topic, file in self.links.items():
            if topic not in resolved_topics:
                logger.warning(f"Unresolved topic: {topic} in file {file}")
                unresolveds.append(f"{topic} ({file})")

            if topic in conflicts_set:
                conflicting = conflicts_set[topic]
                logger.warning(
                    f"In file {file}, topic #{topic} is ambiguous among those files: {', '.join(conflicting)}"
                )
                conflicts.append(f"{file}#{topic} - {', '.join(conflicting)}")

        (Path(self.outdir) / "unresolved.txt").write_text("\n".join(unresolveds))
        (Path(self.outdir) / "conflicts.txt").write_text("\n".join(conflicts))

        total_links = len(self.links)
        valid = True
        if len(unresolveds) > 0:
            logger.error(f"Found {len(unresolveds)} / {total_links} unresolved topics")
            valid = False

        if len(conflicts) > 0:
            logger.error(f"Found {len(conflicts)} / {total_links} ambiguous topics")
            valid = False

        return valid

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
        "parallel_write_safe": False,
    }
