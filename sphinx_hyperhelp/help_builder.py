from __future__ import annotations

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
from .hyperhelp import HelpFile, HelpIndex, HelpTopic

logger = logging.getLogger(__name__)


class HyperHelpBuilder(TextBuilder):
    name = "hyperhelp"
    format = "text"
    epilog = __(
        "The hyperhelp files are in %(outdir)s, index at %(outdir)s/hyperhelp.json"
    )

    out_suffix = ".txt"
    allow_parallel = True
    default_translator_class = HyperHelpTranslator  # type: ignore

    current_docname: str = ""
    current_helpfile: HelpFile = None  # type: ignore
    index: HelpIndex = None  # type: ignore
    links: dict[str, str] = {}
    _translator: HyperHelpTranslator = None  # type: ignore
    _resolved_topics: dict[str, str] = {}  # uri to file

    def prepare_writing(self, docnames):
        self.writer = HyperHelpWriter(self)
        config = self.config
        description = config.epub_description or config.html_title
        # print(
        #     {k: v[0] for k, v in config.values.items() if not callable(v[0]) and v[0]}
        # )
        self.index = HelpIndex(config.project, description, Path(self.outdir))
        self.links = {}
        # TODO: StandaloneHTMLBuilder creates an index page for each html_domain_indices.
        # See eg: https://www.sphinx-doc.org/en/master/py-modindex.html
        # I think we should add this to HyperHelp.

    # TODO: edit reload existing index, and override get_outdated_docs
    # to keep unchanged files in the index
    def get_outdated_docs(self) -> Iterator[str]:
        yield from self.env.found_docs

    def get_target_uri(self, docname: str, typ: str = None) -> str:
        return docname + ".txt"

    def get_relative_uri(self, from_: str, to: str, typ: str = None) -> str:
        # ignore source path, Hyperhelp only has absolute paths
        # This is used when generating toctree.
        return self.get_target_uri(to, typ)

    def finish(self) -> None:
        if self.config.hyperhelp_prune_topics:
            self.index = self.index.prune(set(self.links.keys()))
        valid = self.validate()
        self.index.save()
        if not valid:
            logger.error("The index seems invalid, some topics may be missing")

    def validate(self) -> bool:
        all_topics = [
            (file, help_topic)
            for file, hf in self.index.help_files.items()
            for help_topic in hf.topics
        ]
        resolved_topics: dict[str, str] = {}
        # files are they own topics
        for file in self.index.help_files.keys():
            resolved_topics[file] = file

        conflicts_set: dict[str, set[str]] = defaultdict(set)
        for file, help_topic in all_topics:
            topic = help_topic.topic
            conflict = resolved_topics.get(topic)
            if conflict:
                conflicts_set[topic].add(conflict)
                conflicts_set[topic].add(file)

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

        # TODO: also validate the index:
        # https://github.com/STealthy-and-haSTy/hyperhelpcore/blob/master/all/hyperhelpcore/index_validator.py
        # Notably we should remove aliases that aren't used in practices.
        return valid

    def write_doc(self, docname: str, doctree: Node) -> None:
        assert docname
        self.current_helpfile = HelpFile()
        target = self.get_target_uri(docname)
        self.index.help_files[target] = self.current_helpfile

        super().write_doc(docname, doctree)

    def add_topic(
        self, topic: str, caption: str = "", aliases: list[str] = []
    ) -> HelpTopic:
        caption = caption or topic
        target = self.get_target_uri(self.current_docname)
        conflict = self._resolved_topics.get(topic)
        if conflict:
            # TODO: We actually have a lot of conflict because we generate topic
            # for each title. Some of those titles are never referenced, or are
            # referenced only in ToC.
            # We should try to use more precise uri for ToC and generate less aliases.
            # logger.warning(f"conflict for topic {topic} (from files {target} and {conflict}")
            pass

        more_aliases = []
        for alias in [topic] + aliases:
            self._resolved_topics[alias] = target
            more_aliases.append("/".join((target, alias)))

        help_topic = HelpTopic(topic, caption=caption, aliases=aliases + more_aliases)
        self.current_helpfile.topics.append(help_topic)
        return help_topic


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_builder(HyperHelpBuilder)

    app.add_config_value("hyperhelp_prune_topics", True, "env", str)

    return {
        "version": "builtin",
        "parallel_read_safe": True,
        "parallel_write_safe": False,
    }
