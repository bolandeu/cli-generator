# Changelog

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
