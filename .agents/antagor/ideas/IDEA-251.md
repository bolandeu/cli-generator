---
id: IDEA-251
title: 'CLI keys: Doppler is the source, a provider reads a shared key name as fallback'
created: '2026-10-19T05:54:11+00:00'
source_project: cli-generator
source_path: /Users/bolandau/Work/tools/cli-generator
status: epic
for_path: /Users/bolandau/Work/tools/cli-generator
triage:
  serves: []
  risks: []
  why: Contract with sysadmin accepted by the Human 2026-10-19; package agents apply
    it through cli-builder Update mode.
  score: 3.0
  route: clarify
  at: '2026-10-19T05:59:56+00:00'
clarify_project: /Users/bolandau/Work/tools/cli-generator
clarify_since: '2026-10-19T05:59:56+00:00'
epic: E-003
before_epic: clarifying
---

§4 links the key rules of the contract (Doppler tools/prd, name = env name, Mac via doppler run, keychain only a dev override). A provider declares a shared Doppler name without CLI prefix (GOOGLE_OAUTH_SERVICE_ACCOUNT_JSON, S3_*, TG_*) as fallback env, so wrappers do not rename. Contract docs/contracts/sysadmin.md, accepted by the Human 2026-10-19.
