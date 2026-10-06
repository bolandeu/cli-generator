# Три имени: package_name, cli_name, dist_name

Статус: accepted (восстановлено по истории)

`package_name` — импорт, keychain, префикс env, каталог `.<package>/`; `cli_name` — команда (`[project.scripts]`), может отличаться; `dist_name` — `[project] name`, по умолчанию `rb-<slug>` (стандарт релиза §10). Дистрибутивное имя рендерится в `_distribution.py` (`DIST_NAME`), потому что у editable-установки пакет не сопоставить с дистрибутивом в рантайме. Рантайм берёт имя команды из установленного console script, а не из `__name__`.
