---
id: IDEA-363
title: 'describe --json: cache dir and non-database env (x-rb-data, x-rb-env)'
created: '2026-10-27T17:49:09+00:00'
source_project: spider
source_path: /Users/bolandau/Work/tools/spider
status: dropped
for_path: /Users/bolandau/Work/tools/cli-generator
reason: 'Deferred, not rejected: template freeze, no package breaks; kept in cli-generator
  docs/plans/freeze-list.md and taken up when the freeze lifts'
---

spider SPIDER-003 (page storage for spider fetch) keeps files in the user cache dir (SPIDER_CACHE_DIR, default platformdirs.user_cache_path) and reads env SPIDER_CACHE_DIR, SPIDER_CACHE_TTL_DAYS, SPIDER_CACHE_MAX_GB. describe --json x-rb-data knows only user_data_dir; x-rb-env lists only db.ENV_VARS (purpose database). The platform does not see these files and env. Ask: a Standard way to declare a cache-dir file family and env vars with a non-database purpose.
