# Опциональные части — вопросы copier, а не удаление файлов

Статус: accepted (восстановлено по истории)

`include_project`, `include_auth`, `include_providers`, `include_http_provider`, `include_db`, `include_skill`, `include_describe`, `include_contracts` включают и выключают части через `copier.yml` (`_exclude` по отрендеренным путям); `dist_name_legacy` ведёт переименование. Значения по умолчанию — ADR 0014. Выключение убирает всю поверхность части — зависимости, команды, тесты, но `auth status` остаётся при `include_auth=false` (стандарт: он есть у каждого CLI). Иначе `copier update` не мог бы вести проект между вариантами, а ветка «без auth» молча ломалась (`ModuleNotFoundError` на `keyring`).
