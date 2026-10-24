# Изменения

Здесь живут предложения изменений (change proposals). Правила создания, имплементации и архивации — в `../AGENTS.md`.

Активные: нет.

Завершённые (в `archive/`):

- `migrate-to-godot/` — перенос игры с Python/Arcade+pymunk на Godot 4.7 с сохранением поведения (завершено 2026-10-24).

## Структура предложения

```
changes/<kebab-case-id>/
├── proposal.md   # ## Why / ## What Changes / ## Impact
├── tasks.md      # ## 1. Implementation / ## 2. Validation (чекбоксы)
├── design.md     # опционально: технические решения и альтернативы
└── spec/
    └── <capability>/spec.md   # дельты: ## ADDED / ## MODIFIED / ## REMOVED Requirements
```

Завершённые и подтверждённые изменения переносятся в `archive/`, их дельты вшиваются в живые спеки `../specs/`.
