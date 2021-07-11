from __future__ import annotations

import collections
import logging
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import sphinx.addnodes
from docutils import nodes
from docutils.nodes import Element, Node, Text
from sphinx.writers.text import TextTranslator, TextWriter

from .hyperhelp import HelpExternal, HelpFile, HelpTopic

if TYPE_CHECKING:
    from .help_builder import HyperHelpBuilder

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEBUG_DOCS: list[str] = []
DEBUG_TOPICS: list[str] = []
# DEBUG_DOCS = ["usage/restructuredtext/domains"]
# DEBUG_TOPICS = ["cross-referencing-syntax"]


def long_re(**named_parts: str):
    """Generates a long regex from its parts."""
    # Check that each indivual part is a valid regex
    parts = named_parts.values()
    for part in parts:
        re.compile(part)
    return re.compile(f"({'|'.join(parts)})")


class TopicRef(str):
    """Represents a topic reference f'|:topic_uri:some description|'

    Hack the len method, to only count the description
    """

    def __len__(self) -> int:
        return len(self.split(":", 2)[-1]) + 1

    def strip(self, chars: str = None) -> TopicRef:
        return self


ANCHOR_NODES = (
    nodes.section,
    nodes.term,
    sphinx.addnodes.desc_signature,
    nodes.definition_list,
)


class HyperHelpTranslator(TextTranslator):
    def __init__(self, document, builder: HyperHelpBuilder):
        self.builder: HyperHelpBuilder = builder
        super().__init__(document, builder)
        self.settings = settings = document.settings
        # TODO: expose this as a Sphinx setting
        self.maxwidth = 80
        lcode = settings.language_code

        # Inspired from LaTeXTranslator, handle the first title as document title.
        self.title_found = False
        self.head: list[str] = []
        self.foot: list[str] = []
        self.body = ""

        self.helpfile: HelpFile = None  # type: ignore

    def visit_document(self, node: Element) -> None:
        super().visit_document(node)
        logger.debug(f"Visiting: {node['source']}")
        assert self.helpfile is None
        self.helpfile = self.builder.current_helpfile
        self.builder._doctree = node
        self.builder._translator = self
        if self.builder.current_docname in DEBUG_DOCS:
            breakpoint()

    def depart_document(self, node: Element) -> None:
        super().depart_document(node)
        # This just has been set
        body = self.body
        assert self.helpfile is not None
        self.helpfile = None  # type: ignore
        head, foot = ["".join(lines).strip() for lines in (self.head, self.foot)]
        if not foot.endswith("\n"):
            foot += "\n"
        self.body = "\n\n".join(part for part in (head, body, foot) if part)

    @property
    def current_indent(self) -> int:
        return sum(self.stateindent)

    def end_state(
        self, wrap: bool = True, end: list[str] = [""], first: str = None
    ) -> None:
        """Finalize a block of text by wrapping content if needed"""
        # Copied from TextTranslator. We want to have better control on the wrapping.
        content = self.states.pop()
        maxindent = self.current_indent
        indent = self.stateindent.pop()
        result: list[tuple[int, list[str]]] = []
        toformat: list[str] = []

        def do_format(maxindent: int) -> None:
            if not toformat:
                return
            if wrap:
                res = self.wrap(toformat, width=self.maxwidth)
            else:
                res = "".join(toformat).splitlines()
            if end:
                res += end
            result.append((indent, res))

        for itemindent, item in content:
            # TODO: understand why item is either a str or a list
            if itemindent == -1:
                assert isinstance(item, str)
                toformat.append(item)
            else:
                do_format(maxindent)
                assert isinstance(item, list)
                result.append((indent + itemindent, item))
                toformat = []
        do_format(maxindent)
        if first is not None and result:
            # insert prefix into first line (ex. *, [1], See also, etc.)
            newindent = result[0][0] - indent
            if result[0][1] == [""]:
                result.insert(0, (newindent, [first]))
            else:
                text = first + result[0][1].pop(0)
                result.insert(0, (newindent, [text]))

        self.states[-1].extend(result)

    # Split the generated text into words for wrapping.
    # We need to keep links in one piece.
    wordsep_re = long_re(
        whitespace=r"\s+",
        # hyperhelp_link=r"(?:\|:[^|]+\|)",
        # TODO: do we need this in HyperHelp ?
        interpreted_text=r"(?<=\s)(?::[a-z-]+:)?`\S+",
        hyphenated=r"[^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])",
        em_dash=r"(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w)",
    )

    def get_wrapper(self, width: int = None) -> textwrap.TextWrapper:
        if width is None:
            width = self.maxwidth
        wrapper = textwrap.TextWrapper(width=width, break_long_words=False)
        wrapper.wordsep_re = self.wordsep_re
        return wrapper

    def split(self, fragments: list[str] | str, wrapper=None) -> list[str]:
        if isinstance(fragments, str):
            fragments = [fragments]
        if wrapper is None:
            wrapper = self.get_wrapper()
        chunks: list[str] = []
        for fragment in fragments:
            if isinstance(fragment, TopicRef):
                # Don't split references
                chunks.append(fragment)
            else:
                fragment = wrapper._munge_whitespace(fragment)
                chunks.extend(wrapper._split(fragment))
        return chunks

    def wrap(self, fragments: list[str], width: int) -> list[str]:
        # We don't directly call wrapper.wrap, but do our own splitting instead
        # This allows to not split in the middle of a link.
        # TODO: would it be better to inherit from TextWrapper instead ?
        # TODO: sphinx has a custom _wrap_chunks that handle utf-8 combining chars
        # I've disabled it because using `len` to compute the visible len of strings
        # allows to override it in `TopicRef` class.
        wrapper = self.get_wrapper(width)
        chunks = self.split(fragments)
        return wrapper._wrap_chunks(chunks)

    def visit_desc_signature(self, node: Element) -> None:
        super().visit_desc_signature(node)
        if not node["ids"]:
            return

        topic = node["ids"][0]
        if topic in DEBUG_TOPICS:
            breakpoint()
        self.builder.add_topic(topic)
        # TODO: should we use a more explicit alias here ?
        self.add_text(f"*{topic}:")

    def depart_desc_signature(self, node: Element) -> None:
        topic = node["ids"]
        if topic:
            self.add_text("*")
        super().depart_desc_signature(node)

    visit_term = visit_desc_signature
    depart_term = depart_desc_signature
    visit_definition_list = visit_desc_signature
    depart_definition_list = depart_desc_signature

    def visit_literal_block(self, node: Element, language: str = "rst"):
        if not language:
            language = node["classes"][1] if "code" in node["classes"] else ""
            if "language" in node:
                language = node["language"]
        # De-indent block of codes
        self.new_state(-self.current_indent)
        self.add_text("```" + language + "\n")

    def depart_literal_block(self, node):
        self.add_text("\n```\n")
        super().depart_literal_block(node)

    def visit_doctest_block(self, node):
        self.visit_literal_block(node, "python")

    depart_doctest_block = depart_literal_block

    def visit_section(self, node: Element) -> None:
        if self.title_found:
            # Don't treat the first section as a section
            super().visit_section(node)

    def add_title_as_topic(self, node: Element) -> Optional[str]:
        assert self.helpfile
        parent = node.parent
        if not parent["ids"]:
            logger.debug(f"No ids for node: {parent} in {self.helpfile}")
            return None

        if any(alias in DEBUG_TOPICS for alias in parent["ids"]):
            breakpoint()

        topic, aliases = parent["ids"][0], parent["ids"][1:]
        help_topic = self.builder.add_topic(
            topic, caption=node.astext(), aliases=aliases
        )
        return topic

    def visit_title(self, node: Element) -> None:
        # Note: not calling super
        if isinstance(node.parent, nodes.Admonition):
            self.add_text(node.astext() + ": ")
            raise nodes.SkipNode
        elif isinstance(node.parent, nodes.section) and not self.title_found:
            return self.visit_document_title(node)

        lvl = self.sectionlevel
        topic = self.add_title_as_topic(node)
        if topic:
            self.add_text(f"{lvl * '#'} {topic}:")
        else:
            self.add_text(f"{lvl * '#'} ")

    def visit_document_title(self, node: Element) -> None:
        """Treats the first title as a document title.

        Inspired from the LaTeXTranslator.
        """
        assert not self.title_found
        assert not self.helpfile.description
        # TODO: use git/file date ?
        title = node.children[0].astext().replace('"', "")
        date = datetime.today()
        self.helpfile.add_description(title)
        self.head.append(f'%hyperhelp title="{title}" date="{date:%Y-%m-%d}"\n')
        # TODO: this should not be collapsed with the upcoming title
        topic = self.add_title_as_topic(node)
        if topic:
            self.head.append(self.make_anchor(topic))

        self.title_found = True
        raise nodes.SkipNode

    def make_anchor(self, topic: str) -> str:
        return f"*|{topic}:⚓|*\n"

    def depart_title(self, node: Element):
        pass

    def dispatch_visit(self, node: Node) -> None:
        if isinstance(node, Element):
            self.detect_isolated_target(node)

        super().dispatch_visit(node)

    def detect_isolated_target(self, node: Element) -> None:
        """Detect isolated <target> nodes, and mark them.

        The actual anchor will be generated later during visit_target
        Most <target> nodes are preceding a title
        and we don't need to generate an extra anchor.
        """
        n = len(node.children)
        for i, target in enumerate(node.children):
            if not isinstance(target, nodes.target):
                continue
            if not target.get("ids") and not target.get("refid"):
                continue
            isolated = True
            if i + 1 < n:
                sibling = node.children[i + 1]
                if isinstance(sibling, ANCHOR_NODES):
                    isolated = False
            target.attributes["isolated"] = isolated

    def visit_target(self, node: Element) -> None:
        isolated = node.get("isolated", False)
        if not isolated:
            raise nodes.SkipNode
        topic = node.get("refid") or node["ids"][0]
        if topic:
            self.builder.add_topic(topic)
            self.add_text(self.make_anchor(topic))

    def depart_target(self, node: Element) -> None:
        pass

    def uri2external(self, node: Element) -> Optional[str]:
        uri = node.get("refuri")
        if not uri:
            return None
        if uri.startswith("mailto:"):
            return None
        topic = uri.split("://")[-1].strip("/")
        # TODO? ping the uri to fetch page title and description ?
        # TODO: prevent duplicate
        self.builder.index.externals[uri] = HelpExternal(topic, uri, caption=uri)
        return topic

    def uri2topic(self, node: Element) -> Optional[str]:
        # Replace 'refuri' in reference with HTTP address, if possible
        # None for no possible address
        uri = node.get("refuri")
        if uri:
            # this is a global ID
            if uri.startswith("#"):
                topic = uri[1:]
            elif "#" in uri:
                topic = uri.replace("#", "/")
            else:
                topic = uri
        else:
            topic = node.get("refid")
        if not topic:
            return None
        if topic in DEBUG_TOPICS:
            breakpoint()

        self.builder.links[topic] = self.builder.current_docname
        assert "/../" not in topic
        assert "#" not in topic
        return topic

    def visit_reference(self, node: Element) -> None:
        if "internal" in node:
            internal = node["internal"]
        elif "refuri" in node:
            # Not all nodes have the "internal" field set
            external = (
                node["refuri"].startswith("https://")
                or node["refuri"].startswith("http://")
                or node["refuri"].startswith("mailto:")
            )
            internal = not external
        elif "refid" in node:
            internal = True
        else:
            assert False, f"Invalid reference node: {node} ({node.attributes})"

        if internal:
            topic = self.uri2topic(node)
        else:
            topic = self.uri2external(node)

        # If no target possible, pass through.
        if topic is None:
            return
        text = "".join((c.astext() for c in node.children)).replace("|", "/")
        self.add_text(TopicRef(f"|:{topic}:{text}|"))
        raise nodes.SkipNode

    visit_strong = TextTranslator.visit_emphasis
    depart_strong = TextTranslator.visit_emphasis
    visit_literal_strong = TextTranslator.visit_emphasis
    depart_literal_strong = TextTranslator.visit_emphasis


class HyperHelpWriter(TextWriter):

    supported = ("hyperhelp",)
    """Formats this writer supports."""

    output = ""
    """Final translated form of `document`."""

    translator_class = HyperHelpTranslator
