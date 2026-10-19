# Опциональные части — вопросы copier, а не удаление файлов

Статус: accepted (восстановлено по истории)

`include_auth`, `include_providers`, `include_http_provider`, `include_db`, `include_ci`, `dist_name_legacy` включают и выключают части через `copier.yml` (`_exclude` по отрендеренным путям). Выключение убирает всю поверхность части — зависимости, команды, тесты, но `auth status` остаётся при `include_auth=false` (стандарт: он есть у каждого CLI). Иначе `copier update` не мог бы вести проект между вариантами, а ветка «без auth» молча ломалась (`ModuleNotFoundError` на `keyring`).
