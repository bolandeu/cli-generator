#!/bin/sh
# deploy_command Antagor (`antagor publish`): push main с тегами и уведомление корневого агента tools.
# Antagor запускает команды без shell, поэтому && и stdin живут здесь. ANTAGOR_VERSION — новый тег.
set -e
git push origin main --follow-tags
n="$(git rev-parse --show-toplevel)/../scripts/notify_release.sh"
[ -x "$n" ] || n="$HOME/Work/tools/scripts/notify_release.sh"
sha="$(git rev-parse HEAD)"
# сбой уведомления publish не блокирует
[ -x "$n" ] && { echo "refs/tags/$ANTAGOR_VERSION $sha refs/tags/$ANTAGOR_VERSION 0000000000000000000000000000000000000000" | "$n" cli-generator || true; }
exit 0
