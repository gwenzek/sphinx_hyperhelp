# from __future__ import annotations
# TODO: func_argparse doesn't work with python 3.10

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Union

import func_argparse

logger = logging.getLogger("sphinx_hyperhelp")

BUILD_DIR = Path(".") / "build"
REPOS_DIR = Path(".") / "repos"

# TODO: can we do better to distribute packages ?
FAMOUS_REPOS = {
    # This is the version shipping with Sublime Text
    "PythonDocs": ("https://github.com/python/cpython", "v3.8.8"),
    "Sphinx": ("https://github.com/sphinx-doc/sphinx.git", ""),
}


def resolve_subl() -> Path:
    home = Path(os.environ["HOME"])
    # TODO: make this work for all OSes
    # TODO: add support for "Portable install"
    return home / "Library/Application Support/Sublime Text/Packages/"


def download(name: str, repo: str = "", tag: str = "") -> Path:
    srcdir = REPOS_DIR / name
    REPOS_DIR.mkdir(exist_ok=True)

    if srcdir.exists():
        return srcdir

    if name in FAMOUS_REPOS:
        famous_repo, famous_tag = FAMOUS_REPOS[name]
        repo = repo or famous_repo
        tag = tag or famous_tag

    clone_cmd = ["git", "clone", "--depth=2", repo, str(srcdir)]
    if tag:
        clone_cmd.insert(2, f"--branch={tag}")
    subprocess.run(clone_cmd, check=True)
    return srcdir


def build(name: str, repo: str = "", tag: str = "", outdir: Path = None) -> Path:
    """Builds a Sphinx projects documentation into a Sublime Text package.

    - name: name of the output ST package
      Be careful to not create conflicts with other packages
    - repo: git repository of the project to build documentation from
    - tag: specific git tag/branch/commit to fetch. Defaults to the `master` branch of the repo.
    """
    srcdir = download(name, repo, tag)
    docdir = srcdir / "doc"
    assert docdir.exists(), f"No documentation folder found at {docdir}"
    outdir = outdir or BUILD_DIR / name

    sphinx_cmd: list[Union[str, Path]] = [sys.executable, "-m", "sphinx", "-P"]
    sphinx_cmd += ["-b=hyperhelp", srcdir / "doc", outdir / "hyperhelp"]
    subprocess.run(sphinx_cmd, check=True)
    logger.info(f"Build Package {name} to {outdir}")

    return outdir


def install(name: str, repo: str = "", tag: str = "", outdir: Path = None) -> Path:
    outdir = build(name, repo, tag, outdir)
    package_dir = resolve_subl() / name
    if package_dir.exists():
        if package_dir.resolve() != outdir.resolve():
            raise Exception(
                f"Sublime Text Package {name} already exists at {package_dir}"
            )
    else:
        # TODO: should we directly generate the files there instead ?
        package_dir.link_to(outdir)
    _run_subl_command("hyperhelp_author_reload_index_by_name", package=name)
    logger.info(f"Will try to open documentation {name} in Sublime Text.")
    _run_subl_command("hyperhelp_topic", package=name, topic="contents.txt")
    logger.info(f"Installed Package {name} to {package_dir}.")
    return package_dir


def _run_subl_command(command, **args):
    subprocess.run(["subl", "--command", " ".join((command, json.dumps(args)))])


def _dispatch(
    name: str,
    repo: str = "",
    tag: str = "",
    outdir: Path = None,
    action: str = "install",
) -> None:
    """Builds a Sphinx projects documentation and install it as a Sublime Text package.

    - name: name of the output ST package
      Be careful to not create conflicts with other packages
    - repo: git repository of the project to build documentation from
    - tag: specific git tag/branch/commit to fetch. Defaults to the `master` branch of the repo.
    - outdir: folder where to generate the documentation
    - action: install/build/download
    """
    actions = {fn.__name__: fn for fn in [install, build, download]}
    if action not in actions:
        raise ValueError(f"Unknown action {action!r}, chose from {set(actions.keys())}")

    actions[action](name, repo, tag, outdir)  # type: ignore


def main():
    func_argparse.single_main(_dispatch)
