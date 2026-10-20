"""Run `copier update` on a tree that is staged but not committed.

For a worker that may not `git commit`: copier refuses a dirty tree and has no flag to skip that
check. Copier builds its merge base from the index (`git write-tree`), so a staged tree loses
nothing. This script stages the tree (`git add -A`), switches only the dirty-tree guard off, and
passes every argument to `copier update`.

    uvx --from copier python <skill dir>/scripts/copier_update_staged.py [copier update args]

Exit code is copier's; non-zero on any copier error. On a clean tree nothing is staged and the
run is a plain `copier update`.
"""

import subprocess
import sys

from copier._cli import CopierApp
from copier._subproject import Subproject


def main(argv: list[str]) -> int:
    subprocess.run(["git", "add", "-A"], check=True)
    # The one touch of copier internals, checked against copier 9.19.1 (Subproject.is_dirty,
    # called in Worker.run_update).
    Subproject.is_dirty = lambda self: False
    _, code = CopierApp.run(["copier", "update", *argv], exit=False)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
