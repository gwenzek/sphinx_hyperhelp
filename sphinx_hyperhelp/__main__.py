# from __future__ import annotations
# TODO: func_argparse doesn't work with python 3.10

import os
import subprocess
import sys
from pathlib import Path


import func_argparse
import json
from typing import Union

BUILD_DIR = Path(__file__).parent.parent / "build"
REPOS_DIR = Path(__file__).parent.parent / "repos"

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


def show_unresolved_diff(unresolved: Path, unresolved_prev: Path) -> None:
    count = len(unresolved.read_text().splitlines())
    if not unresolved_prev.exists():
        unresolved_prev.write_text("")
    prev_count = len(unresolved_prev.read_text().splitlines())
    # unresolved_diff = subprocess.check_output(
    #     ["diff", unresolved, unresolved_prev], text=True
    # )
    # short_diff = "\n".join(unresolved_diff.splitlines()[:10])
    print(f"Went from {prev_count} to {count} unresolved links. Diff:")
    # print(short_diff)


def build(name: str, repo: str = "", tag: str = "") -> Path:
    """Builds a Sphinx projects documentation into a Sublime Text package.

    - name: name of the output ST package
      Be careful to not create conflicts with other packages
    - repo: git repository of the project to build documentation from
    - tag: specific git tag/branch/commit to fetch. Defaults to the `master` branch of the repo.
    """
    srcdir = download(name, repo, tag)
    docdir = srcdir / "doc"
    assert docdir.exists(), f"No documentation folder found at {docdir}"
    outdir = BUILD_DIR / name / "hyperhelp"

    unresolved = outdir / "unresolved.txt"
    unresolved_prev = outdir / "unresolved_prev.txt"
    if unresolved.exists():
        unresolved.rename(unresolved_prev)

    sphinx_cmd: list[Union[str, Path]] = [sys.executable, "-m", "sphinx", "-P"]
    sphinx_cmd += ["-b=hyperhelp", srcdir / "doc", outdir]
    subprocess.run(sphinx_cmd, check=True)

    show_unresolved_diff(unresolved, unresolved_prev)
    package_dir = resolve_subl() / name
    if package_dir.exists():
        if package_dir.resolve() != outdir.parent:
            raise Exception(
                f"Sublime Text Package {name} already exists at {package_dir}"
            )
    else:
        package_dir.link_to(outdir.parent)
    # TODO: trigger help reload ?
    hyperhelp_topic_args = {"package": name, "topic": "contents.txt"}
    subprocess.run(
        [
            "subl",
            "--command",
            "hyperhelp_topic " + json.dumps(hyperhelp_topic_args),
        ]
    )
    return outdir


def main():
    func_argparse.single_main(build)
