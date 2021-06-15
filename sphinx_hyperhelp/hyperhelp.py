from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple


class HelpTopic(NamedTuple):
    topic: str
    caption: str
    aliases: list[str] = []

    def as_json(self) -> dict:
        d: dict = {"topic": self.topic, "caption": self.caption}
        if self.aliases:
            d["aliases"] = self.aliases
        return d

    @staticmethod
    def from_json(topic: dict) -> HelpTopic:
        return HelpTopic(**topic)


class HelpFile:
    def __init__(self, module: str, description: str = ""):
        self.module = module
        self.description = description
        self.topics: list[HelpTopic] = []
        self.sources: dict[str, HelpFile] = {}
        self.toctree: list[Path] = []

    def __repr__(self) -> str:
        return f"HelpFile({self.module!r}, {self.description!r})"

    def as_json(self) -> list:
        if not self.description and not self.topics:
            return []
        return [self.description] + [t.as_json() for t in self.topics]  # type: ignore

    def add_topic(self, name: str, aliases: list[str] = []) -> None:
        if not aliases:
            qualified_name = f"{self.module}/{name}"
            aliases = [qualified_name]
        self.topics.append(HelpTopic(name, name, aliases=aliases))

    def add_description(self, description: str) -> None:
        assert not self.description, f"{self} already got a description"
        self.description = description

    def add_source(self, name: str) -> None:
        # TODO
        # file = HelpFile("TODO", name)
        # file.topics.append(HelpTopic(name))
        # self.sources[SOURCE_PREFIX_URL + name] = file
        ...


class HelpExternal(NamedTuple):
    description: str
    topic: str
    caption: str

    def as_json(self) -> list:
        return [self.description, {"topic": self.topic, "caption": self.caption}]


class HelpIndex(NamedTuple):
    package: str
    description: str
    doc_root: Path
    help_files: dict[str, HelpFile] = {}
    externals: dict[str, HelpExternal] = {}

    def as_json(self) -> dict:
        externals = {url: v.as_json() for url, v in self.externals.items()}
        help_files = {
            k: v.as_json() for (k, v) in self.help_files.items() if v.description
        }
        return {
            "package": self.package,
            "description": self.description,
            "doc_root": f"{self.doc_root.name}/",
            "help_files": help_files,
            "externals": externals,
            "help_contents": list(self.help_files.keys()),
        }

    def save(self) -> Path:
        output = self.path()
        output.write_text(json.dumps(self.as_json(), indent=2))
        return output

    def path(self) -> Path:
        return self.doc_root / "hyperhelp.json"
