#!/usr/bin/env python3
"""Clone a directory tree without copying files.

The script walks a source directory, skips directories ignored by git, and then
either creates the same directory tree under a target directory or prints a
portable shell script with mkdir commands.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def resolve_git_root(path: Path) -> Path:
    result = run_git(["rev-parse", "--show-toplevel"], path)
    if result.returncode != 0:
        raise RuntimeError(
            f"{path} is not inside a git repository: {result.stderr.strip()}"
        )
    return Path(result.stdout.strip()).resolve()


def is_git_ignored(git_root: Path, path: Path) -> bool:
    rel_path = path.resolve().relative_to(git_root).as_posix()
    result = run_git(["check-ignore", "-q", "--", rel_path], git_root)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise RuntimeError(
        f"git check-ignore failed for {rel_path}: {result.stderr.strip()}"
    )


def iter_visible_dirs(source_root: Path, git_root: Path) -> list[Path]:
    visible_dirs: list[Path] = []

    for current_root, dir_names, _file_names in os.walk(source_root, topdown=True):
        current_path = Path(current_root)
        kept_names: list[str] = []

        for dir_name in sorted(dir_names):
            dir_path = current_path / dir_name
            if dir_name == ".git" or is_git_ignored(git_root, dir_path):
                continue

            kept_names.append(dir_name)
            visible_dirs.append(dir_path.relative_to(source_root))

        dir_names[:] = kept_names

    return visible_dirs


def create_dirs(target_root: Path, relative_dirs: list[Path]) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    for relative_dir in relative_dirs:
        (target_root / relative_dir).mkdir(parents=True, exist_ok=True)


def emit_shell(relative_dirs: list[Path], target_prefix: str) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
    ]

    if target_prefix:
        lines.append(f"mkdir -p -- {shlex.quote(target_prefix)}")

    for relative_dir in relative_dirs:
        path = Path(target_prefix) / relative_dir if target_prefix else relative_dir
        lines.append(f"mkdir -p -- {shlex.quote(path.as_posix())}")

    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Clone the directory structure of a git working tree while excluding "
            "git-ignored directories. Files are never copied."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path.cwd(),
        help="source directory to scan; defaults to the current directory",
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="target directory to create; required unless --emit-shell is used",
    )
    parser.add_argument(
        "--emit-shell",
        action="store_true",
        help="print mkdir commands instead of creating directories",
    )
    parser.add_argument(
        "--target-prefix",
        default="",
        help="prefix used in emitted mkdir commands, for example repo-name",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    source_root = args.source.expanduser().resolve()

    if not source_root.is_dir():
        print(f"source is not a directory: {source_root}", file=sys.stderr)
        return 2

    if not args.emit_shell and args.target is None:
        print("--target is required unless --emit-shell is used", file=sys.stderr)
        return 2

    target_root = args.target.expanduser().resolve() if args.target is not None else None
    if not args.emit_shell and target_root == source_root:
        print(
            "warning: --source and --target point to the same directory; "
            "this only recreates directories already present. For GitHub or "
            "Codespace, run --emit-shell on the original local source and "
            "execute the generated mkdir script remotely.",
            file=sys.stderr,
        )

    try:
        git_root = resolve_git_root(source_root)
        relative_dirs = iter_visible_dirs(source_root, git_root)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.emit_shell:
        print(emit_shell(relative_dirs, args.target_prefix), end="")
        return 0

    assert target_root is not None
    create_dirs(target_root, relative_dirs)
    print(f"created {len(relative_dirs)} directories under {target_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
