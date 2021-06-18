import func_argparse
import os
import subprocess
import sys
from pathlib import Path

BUILD_DIR = Path(__file__).parent.parent / "build"
REPOS_DIR = Path(__file__).parent.parent / "repos"


def resolve_subl() -> Path:
    home = Path(os.environ["HOME"])

    return home / "Library/Application Support/Sublime Text/Packages/"


def download(name: str, repo: str, tag: str = "") -> Path:
    srcdir = REPOS_DIR / name
    REPOS_DIR.mkdir(exist_ok=True)

    if srcdir.exists():
        return srcdir

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
    unresolved_diff = subprocess.check_output(
        ["diff", unresolved, unresolved_prev], text=True
    )
    short_diff = "\n".join(unresolved_diff.splitlines()[:10])
    print(f"Went from {prev_count} to {count} unresolved links. Diff:")
    print(short_diff)


def build(name: str, repo: str, tag: str = "") -> Path:
    """Builds a Sphinx projects documentation into a Sublime Text package.

    - name: name of the output ST package
      Be careful to not create conflicts with other packages
    - repo: git repository of the project to build documentation from
    - tag: specific git tag/branch/commit to fetch. Defaults to the `master` branch of the repo.
    """
    srcdir = download(name, repo, tag)
    outdir = BUILD_DIR / name / "hyperhelp"

    unresolved = outdir / "unresolved.txt"
    unresolved_prev = outdir / "unresolved_prev.txt"
    if unresolved.exists():
        unresolved.rename(unresolved_prev)

    sphinx_args = ["-P", "-b", "hyperhelp", srcdir / "doc", outdir]
    subprocess.run([sys.executable, "-m", "sphinx"] + sphinx_args, check=True)

    show_unresolved_diff(unresolved, unresolved_prev)
    # TODO: link the helps file into ST directory
    # TODO: trigger help reload ?
    # TODO: open help in ST
    return outdir


def main():
    func_argparse.single_main(build)
