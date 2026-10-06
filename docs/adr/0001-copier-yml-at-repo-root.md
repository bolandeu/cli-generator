# copier.yml лежит в корне репозитория

Статус: accepted (восстановлено по истории)

Репозиторий — и плагин (`skills/`, `.claude-plugin/`), и шаблон. Copier 9.x не имеет флага `--subdirectory`, поэтому `copier.yml` живёт в корне с `_subdirectory: template`; внутри `template/` он не заработает. Так шаблон отделён от файлов плагина при генерации.
