"""copier migration (after an update): a package's own edits to its old copy of the gate become a conflict.

Up to v1.20.10 the template copied the gate into scripts/release.py; now a package runs it through uvx and
`copier update` deletes the copy. A copy the package edited comes back, marked unmerged and deleted by the
template, so `git status` shows it: stage 1 is the template's copy at the last update, stage 2 the package's.

    python <template>/scripts/keep_edited_gate_copy.py <template> <template ref of the last update>

Run in the package by copier.yml's `_migrations`; exit code 0 unless git fails.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

COPY = "scripts/release.py"


def _git(*args: str, cwd: str = ".", stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=cwd, input=stdin, capture_output=True, check=False)  # noqa: S603, S607


def main(template: str, last: str) -> int:
    base = _git("show", f"{last}:template/{COPY}", cwd=template)
    ours = _git("show", f":{COPY}")  # the index: the package's copy as committed or staged before the update
    if base.returncode or ours.returncode or ours.stdout == base.stdout:
        return 0  # no copy, or the package never edited it: the deletion stands
    mode = _git("ls-files", "--stage", "--", COPY).stdout.decode().split()[0]
    Path(COPY).write_bytes(ours.stdout)
    blobs = [
        _git("hash-object", "-w", "--stdin", stdin=blob).stdout.decode().strip() for blob in (base.stdout, ours.stdout)
    ]
    entries = f"0 {'0' * 40}\t{COPY}\n{mode} {blobs[0]} 1\t{COPY}\n{mode} {blobs[1]} 2\t{COPY}\n"
    if _git("update-index", "--index-info", stdin=entries.encode()).returncode:
        return 1
    print(  # noqa: T201
        f"{COPY}: the package edited its copy of the gate; the template no longer ships it (the gate runs through "
        "uvx). Kept as a conflict: move the edits into a ticket to cli-generator, then `git rm` the file.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
