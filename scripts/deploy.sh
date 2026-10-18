#!/bin/sh
# deploy_command Antagor (`antagor publish`): push main с тегами в origin (Gitea).
# Antagor запускает команды без shell, поэтому && живёт здесь.
set -e
git push origin main --follow-tags
