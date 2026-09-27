#!/usr/bin/env bash
# (Re)install this repo's git hooks. .git/hooks/ is not tracked by git, so
# hooks are lost on every fresh clone — re-run this after cloning, or any
# time a hook seems to be missing.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hook_path="$repo_root/.git/hooks/pre-commit"

cat > "$hook_path" <<'EOF'
#!/usr/bin/env bash
root="$(git rev-parse --show-toplevel)"
python3 "$root/scripts/check_command_docstrings.py"
python3 "$root/scripts/check_changelog_fragment.py"
exit 0
EOF

chmod +x "$hook_path"
echo "Installed pre-commit hook -> $hook_path"
