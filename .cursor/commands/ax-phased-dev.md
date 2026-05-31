# AX: поэтапная разработка X++ (`/ax-phased-dev`)

Пошаговая реализация по постановке с **gate** между фазами и **xpp-review** после каждого этапа с кодом.

**Скилл:** `.cursor/skills/ax-phased-dev-pipeline/SKILL.md` — выполнять протокол оттуда полностью.

**Рабочая директория:** корень `DynamicsAX`.

---

## Как вызвать

Скопируй шаблон, подставь значения. Постановка — **файл** или **текст** в `<<< >>>`.

```text
/ax-phased-dev

PROJECT_ID: MRC_MERK_000002479_01
PROJECT_FOLDER: MRC_MERK_000002479_01NewUPDNumder
XPO: XPO/SharedProject_MRC_MERK_000002479_01.xpo
     (или: извлечь из CUS по indexXPO_cus)

Постановка (вариант A — файл):
@Projects/MRC_MERK_000002479_01NewUPDNumder/Documentation/task.md

Постановка (вариант B — текст с клавиатуры):
<<<
Вставь сюда полный текст задачи без файла.
>>>

Начни с фазы 0. Следующие фазы — только по моим командам «фаза N» / «продолжай».
Сборку *_WR.xpo (/xpo-roundtrip) не делать без моей явной команды.
```

---

## Режим (кратко для агента)

1. **Фаза 0:** `/xpo-index-check`, `comment_rules` + `commentmeta.json`, план фаз в чате — **без правок `.xpp`**.
2. **Фазы 1…:** только по команде `фаза N`; после фазы с кодом — субагент **xpp-review**, правки до `critical=0`, `medium=0`.
3. **WR / roundtrip** — только по «собери WR» / `/xpo-roundtrip`.
4. Разведка без кода — отдельно **`/ax-investigation`** → `investigationTask.md`.

---

## Отличие от `/ax-investigation`

| | `/ax-investigation` | `/ax-phased-dev` |
|---|---------------------|------------------|
| Код | запрещён | по фазам, с review |
| Результат | `investigationTask.md` | отчёты в чате (+ опционально `todoList.md` в проекте) |
| Переход дальше | по завершении отчёта | **только** по команде пользователя |
