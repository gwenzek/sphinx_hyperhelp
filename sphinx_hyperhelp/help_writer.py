from __future__ import annotations
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from docutils import nodes
from docutils.nodes import Element, Node, Text
from sphinx.writers.text import TextTranslator, TextWrapper, TextWriter

from .hyperhelp import HelpExternal, HelpFile

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEBUG_DOCS: list[str] = []
DEBUG_TOPICS: list[str] = []
# DEBUG_DOCS = ["usage/restructuredtext/domains"]
# DEBUG_TOPICS = ["cross-referencing-python-objects"]


def long_re(**named_parts: str):
    """Generates a long regex from its parts."""
    # Check that each indivual part is a valid regex
    parts = named_parts.values()
    for part in parts:
        re.compile(part)
    return re.compile(f"({'|'.join(parts)})")


class HyperHelpTranslator(TextTranslator):
    def __init__(self, document, builder=None):
        super().__init__(document, builder)
        self.settings = settings = document.settings
        # TODO: expose this as a Sphinx setting
        self.maxwidth = 80
        lcode = settings.language_code

        # Warn only once per writer about unsupported elements
        self._warned = set()
        # Lookup table to get section list from name
        self.head, self.foot = [], []
        self.body = ""

        self.helpfile: HelpFile = None

    def visit_document(self, node: Element) -> None:
        super().visit_document(node)
        print(node["source"])
        assert self.helpfile is None
        self.helpfile = self.builder.add_help_file()
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

    def end_state(
        self, wrap: bool = True, end: List[str] = [""], first: str = None
    ) -> None:
        # Copied from TextTranslator. We want to have better control on the wrapping.
        content = self.states.pop()
        maxindent = sum(self.stateindent)
        indent = self.stateindent.pop()
        result: List[Tuple[int, List[str]]] = []
        toformat: List[str] = []

        def do_format(maxindent: int) -> None:
            if not toformat:
                return
            if wrap:
                res = self.wrap("".join(toformat), width=self.maxwidth)
            else:
                res = "".join(toformat).splitlines()
            if end:
                res += end
            result.append((indent, res))

        for itemindent, item in content:
            if itemindent == -1:
                toformat.append(item)  # type: ignore
            else:
                do_format(maxindent)
                result.append((indent + itemindent, item))  # type: ignore
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
        hyperhelp_link=r"(?:\|:[^|]+\|)",
        # TODO: do we need this in HyperHelp ?
        interpreted_text=r"(?<=\s)(?::[a-z-]+:)?`\S+",
        hyphenated=r"[^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])",
        em_dash=r"(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w)",
    )

    def get_wrapper(self, width: int = None) -> TextWrapper:
        if width is None:
            width = self.maxwidth
        wrapper = TextWrapper(width=width)
        wrapper.wordsep_re = self.wordsep_re
        return wrapper

    def wrap(self, text: str, width: int) -> List[str]:
        return self.get_wrapper(width).wrap(text)

    def split(self, text: str) -> List[str]:
        return self.get_wrapper()._split(text)

    def visit_desc_signature(self, node: Element) -> None:
        super().visit_desc_signature(node)
        if not node["ids"]:
            return

        topic = node["ids"][0]
        if topic in DEBUG_TOPICS:
            breakpoint()
        self.helpfile.add_topic(topic)
        self.add_text(f"*{topic}:")

    def depart_desc_signature(self, node: Element) -> None:
        topic = node["ids"]
        if topic:
            self.add_text("*")
        super().depart_desc_signature(node)

    visit_definition_list = visit_desc_signature
    depart_definition_list = depart_desc_signature

    def visit_literal_block(self, node: Element, language: str = ""):
        super().visit_literal_block(node)
        if not language:
            language = node["classes"][1] if "code" in node["classes"] else ""
            if "language" in node:
                language = node["language"]
        self.add_text("```" + language + "\n")

    def depart_literal_block(self, node):
        self.add_text("```\n\n")
        super().depart_literal_block(node)

    def visit_doctest_block(self, node):
        self.visit_literal_block(node, "python")

    depart_doctest_block = depart_literal_block

    def visit_block_quote(self, node):
        # TODO: prefix ">" on all lines
        super().visit_block_quote(node)
        self.add_text("> ")

    def add_title_as_topic(self, node: Element) -> Optional[str]:
        assert self.helpfile
        parent = node.parent
        if not parent["ids"]:
            logger.debug(f"No ids for node: {parent} in {self.helpfile}")
            return None

        # TODO handle aliases. The node['ids'] may have more than one value
        aliases = []
        for topic in parent["ids"]:
            aliases.append(topic)
            aliases.append(self.builder.current_docname + "/" + topic)

        if any(topic in DEBUG_TOPICS for topic in aliases):
            breakpoint()

        self.helpfile.add_topic(aliases[0], aliases[1:])
        return topic

    def visit_title(self, node: Element):
        # Note: not calling super
        if isinstance(node.parent, nodes.Admonition):
            self.add_text(node.astext() + ": ")
            raise nodes.SkipNode

        title = node.children[0].astext().replace('"', "")

        # TODO: understand how this incremented / decremented
        lvl = self.sectionlevel
        if lvl == 0:
            breakpoint()

        if lvl == 1 and not self.helpfile.description:
            # Document heading
            # TODO: use git/file date ?
            date = datetime.today()
            self.helpfile.add_description(title)
            self.head.append(f'%hyperhelp title="{title}" date="{date:%Y-%m-%d}"')
            raise nodes.SkipNode

        # TODO: reuse topic name from rst
        topic = self.add_title_as_topic(node)
        if topic:
            self.add_text(f"{lvl * '#'} {topic}: ")
        else:
            self.add_text(f"{lvl * '#'} ")

    def depart_title(self, node: Element):
        pass

    def uri2topic(self, node) -> Optional[str]:
        # Replace 'refuri' in reference with HTTP address, if possible
        # None for no possible address
        uri = node.get("refuri")

        external = not node.get("internal", False)
        if external:
            if not uri:
                return None
            topic = uri.split("://")[-1].strip("/")
            # TODO? ping the uri to fetch page title and description ?
            # TODO: prevent duplicate
            self.builder.index.externals[uri] = HelpExternal(uri, topic, uri)
            return topic
        current_doc = Path(self.builder.current_docname)

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

        self.builder.links[topic] = current_doc
        assert "/../" not in topic
        assert "#" not in topic
        return topic

    def visit_reference(self, node: Element):
        # If no target possible, pass through.
        topic = self.uri2topic(node)
        if topic is None:
            return
        text = "".join((c.astext() for c in node.children)).replace("|", "/")
        self.add_text(f"|:{topic}:{text}|")
        raise nodes.SkipNode

    def unknown_visit(self, node):
        # TODO: we shouldn't need this.
        # It only triggers when running make build, but not make test.
        node_type = node.__class__.__name__
        # self.document.reporter.warning(f"The {node_type} element not supported: {node.astext()}")
        self.document.reporter.warning(f"The {node_type} element not supported")
        raise nodes.SkipNode


class HyperHelpWriter(TextWriter):

    supported = ("hyperhelp",)
    """Formats this writer supports."""

    output = None
    """Final translated form of `document`."""

    translator_class = HyperHelpTranslator
