# Changelog

## v1.18.1 — 2026-10-18

### Outside epics

- Справка: правки по ревью E-001 — пример не запускает callback, код EXAMPLE_OUTSIDE_PATH, тексты (CG-019)

## v1.18.0 — 2026-10-18

### E-001 — Human help for every CLI: docs command and help standard in the template

Every generated CLI has '<cli> docs': a deterministic OpenCLI document InSpectra renders into a readable HTML page; the help standard lives in reference/help-standard.md and a test enforces it on every command, with a project allowlist for old commands; describe stays the same machine contract plus arity.maximum.
Time: 1.3h since the epic was approved

- Шаблон: тест стандарта справки над каждой командой и allowlist проекта (CG-017)

## v1.17.0 — 2026-10-18

### E-001 — Human help for every CLI: docs command and help standard in the template

Every generated CLI has '<cli> docs': a deterministic OpenCLI document InSpectra renders into a readable HTML page; the help standard lives in reference/help-standard.md and a test enforces it on every command, with a project allowlist for old commands; describe stays the same machine contract plus arity.maximum.
Time: 1.1h since the epic was approved

- Шаблон: команда docs — OpenCLI-документ для InSpectra, describe + arity.maximum (CG-016)
- Справочники: стандарт справки (help-standard.md), docs в architecture/conventions, Update mode (CG-018)

## v1.16.1 — 2026-10-18

### Outside epics

- Публикация: убрать запасной путь new-repo-in-gitea.sh, сообщать sysadmin о новом репо (CG-015)

## v1.16.0 — 2026-10-18

### Outside epics

- Убрать агента tools из навыка, справочников и шаблона; публикация через Gitea (CG-014)

## v1.15.0 — 2026-10-06

### Changed

- Идея: линтер или check для правил httpx-вне-providers и print() (CG-011)
- Шаблон: тест AGENTS.md без магического числа, FAILED в check_template.sh (CG-013)

### Documentation

- Навык: Update mode для проекта со старым скриптом релиза и деплоя (CG-012)

## v1.14.0 — 2026-10-06

### Changed

- Шаблон: убрать мёртвый staged и укрепить default antagor_prefix (CG-008)
- Шаблон: правки CODING_STANDARDS, CONTEXT и README по ревью CG-006 (CG-010)

### Documentation

- Навык и справочники плагина: Antagor вместо towncrier, хуков и ручного релиза (CG-007)

## v1.13.0 — 2026-10-06

### Added

- Шаблон: AGENTS.md и CLAUDE.md проекта — только указатели (CG-009)

## v1.12.0 — 2026-10-06

### Added

- Шаблон: раскладка методологии (AGENTS-указатели, CONTEXT, CODING_STANDARDS, docs/adr) (CG-006)

## v1.11.0 — 2026-10-06

### Added

- Шаблон: .agents/antagor, deploy.sh и вопрос antagor_prefix (CG-005)

## v1.10.0 — 2026-10-06

### Added

- Шаблон: убрать свои хуки проекта (.githooks, install_hooks.sh, .claude/settings.json) (CG-004)

## v1.9.0 — 2026-10-06

### Added

- Шаблон без towncrier и фрагментов, release.py — только --check (CG-003)

## v1.8.3 — 2026-10-06

### Changed

- scripts/deploy.sh: push main+тег и уведомление tools о версии шаблона (CG-002)

## v1.8.2 — 2026-10-06

### Changed

- scripts/check_template.sh: гейт шаблона одной командой (CG-001)
