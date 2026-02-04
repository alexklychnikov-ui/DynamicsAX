# Версионный лог проекта DynamicsAX


## Версия от 2026-02-03 (Job проверки checkBatchOrVolumeGradeAccountin в parserXPO)

**Действие:** В папке parserXPO создан XPO с джобом для проверки метода checkBatchOrVolumeGradeAccountin и заполнения MPSalesPurchMarkCodeTable из XML.

### Сделано:
- **Файл:** `parserXPO/Job_CheckBatchOrVolumeGradeFromXML.xpo`
- **Класс JobCheckBatchOrVolumeGradeRunBase (RunBase):** диалог с полями «XML file» (путь к файлу) и «Sales order» (SalesId). Метод `run()`: загрузка XML из файла в XmlDocument; парсинг DropIDDetails/DropIDDetail по логике readerLinesHonest в таблицу RabbitIntEngineImpInforSalesMPTable; вызов `RabbitIntEngineImp_Infor.checkBatchOrVolumeGradeAccountin(salesId, true)`; запись из salesMPTable в MPSalesPurchMarkCodeTable (SalesPurch::Sales, CustVendAC, ItemId, GTINFromInfor/MPCode и т.д.).
- **Метод readerLinesHonestFromXml:** аналог readerLinesHonest по XML (узлы Sku, Qty, MPCode, GTIN, DropId, InventBatchId, hs_mark_type), заполнение RabbitIntEngineImpInforSalesMPTable. Queue берётся из первой записи RabbitQueue (если есть).
- **Job Job_CheckBatchOrVolumeGradeFromXML:** запуск RunBase через `prompt()` и `run()`.
- Исходные данные (сигнатуры, таблицы, логика) взяты из `XPO/SharedProject_X5SHP_INT_1_000002338_01.xpo`.

### Промпт:
«в папке parserXPO создай новый джоб для проверки работы метода checkBatchOrVolumeGradeAccountin в классе RabbitIntEngineImp_Infor. На входе джоба диалог с выбором файла XML, далее читаем данные метод readerLinesHonest и на выходе заполненная новыми записями таблица MPSalesPurchMarkCodeTable. Все исходные данные в XPO/SharedProject_X5SHP_INT_1_000002338_01.xpo»

---

## Версия от 2026-02-03 (контрольная проверка п.6–13 ToDoList и parserXPO по ТЗ)

**Действие:** Контрольная проверка реализованного кода по пунктам 6–13 ToDoList и соответствия кода в parserXPO техзаданию TS_GTIN_IntegrationAX2012.md.

### Результаты по пунктам 6–13 (формы/UI):
- **П.6–7, 12–13:** Реализованы в XPO (SharedProject_X5SHP_INT_1_000002338_01_WR.xpo), не в parserXPO. Форма MPProductGroup — поле IsAcceptGTINFromInfor; форма MPSalesPurchMarkCodeForm — поле GTINFromInfor, кнопка «Заменить GTIN из Infor по строке» (метка @MIK14664), диалог замены с полями текущий/новый GTIN и валидацией EAN/UCC-14.
- **П.8–11:** Класс MPCreateOrUpdateMarkCodeTableNewRunBase в XPO: dfIsAcceptGTINFromInfor, dfGTINFromInfor, dfAgregationCount; методы dialog, getFromDialog, validate; взаимное исключение — dfMPCode_modified, dfGTINFromInfor_modified, dfAgregationCount_modified, dfIsAcceptGTINFromInfor_modified; запись AgregationCount в таблицу. Соответствует ТЗ разд. 3.1.2.

### Результаты по parserXPO (обработка Infor, п.15–30 ТЗ):
- **readerLinesHonest.xpp:** Чтение тега \<GTIN\> в DropIdDetail, запись в salesMPTable.GTINFromInfor и Qty; поддержка DropIDDetails и bodyTagName. ТЗ п.1, 6–7 — ок.
- **saveMPCode.xpp:** Запись GTINFromInfor, AgregationCount (из Qty), взаимоисключение с MPCode; агрегация по ItemId с суммой Qty для GTIN. ТЗ п.6 — ок.
- **createPickInvoices.xpp:** Вызов checkBatchOrVolumeGradeAccountin(SalesId, true) до цикла по паллетам. ТЗ «сначала проверки, затем запись» — ок.
- **checkBatchOrVolumeGradeAccountin.xpp:** Паттерн MPCodeCustPickingListCheckType/MPCodeCustInvoiceCheckType; проверка ОСУ/выбытия (MPVolumeAndVarietalAccSales, RetirementFromLegalEntity); isAcceptGTINFromInfor; формат 14 цифр (@MIK14633); InventItemGTIN (@MIK14634); запрет ПУ+GTIN по одному артикулу (@MIK14635); логирование 2+ GTIN на SKU (@MIK14636). ТЗ п.2–5, проверки #1–#3 — ок.
- **Замечание по ТЗ п.4:** Ошибки «Присланы не все GTIN. Смешанная отгрузка товара запрещена» и «Отгрузка товара смешанного учёта запрещена» (разные формулировки для «один с GTIN, другой пустой» и «два разных GTIN») в коде не разделены — используется общая проверка по таблице с @MIK14635. При двух разных GTIN на один SKU выполняется только info(@MIK14636), без выброса ошибки «смешанного учёта запрещена» (ТЗ п.4 предписывает выброс).

### Промпт:
«делаем контрольную проверку реализованного кода в папке parserXPO проверяем подробное описание выполненных пунктов в техзадании TS_GTIN_IntegrationAX2012.md»

---

## Версия от 2026-02-03 (xpo_writer: структура XPO и кодировка)

**Действие:** Исправлена запись XPO в xpo_writer.py, чтобы не ломать структуру при импорте в AOT.

### Подробности:
- Чтение XPO с `newline=''` — сохраняются оригинальные переводы строк (CRLF/LF). Запись с `newline=''` — без преобразования.
- Определение `_line_ending` по содержимому (`\r\n` или `\n`); при замене SOURCE-блоков используется тот же разделитель строк.
- Новые методы в элемент больше не добавляются: при отсутствии метода в XPO выполняется только замена существующих, добавление отключено (лишний SOURCE/ENDSOURCE мог ломать импорт).
- Кодировка: по умолчанию cp1251 для чтения/записи (русская AX).
- Промпт: «что-то сломалось в выгруженном файле… ошибка при импортировании в АОТ… вставку или замену производить аккуратно не ломая структуру»

---

## Версия от 2026-02-03 (обработка GTIN в RabbitIntEngineImp_Infor)

**Действие:** Реализованы пункты 15–31 ToDoList: обработка тега `<GTIN>` в разделе DropIdDetail, заполнение RabbitIntEngineImpInforSalesMPTable и запись в MPSalesPurchMarkCodeTable.

### Подробности:
- **readerLinesHonest.xpp:** Чтение тега `<GTIN>` в цикле по DropIdHonestSign; переменная `gtinFromInfor`, инициализация полей строки в начале цикла по дочерним узлам; присвоение `salesMPTable.GTINFromInfor = gtinFromInfor`.
- **saveMPCode.xpp:** Взаимоисключение: при наличии `GTINFromInfor` записываются `codeTable.GTINFromInfor`, `codeTable.AgregationCount` из `Qty`, `codeTable.MPCode = ''`; иначе — марки и CorrectCode/CaseSensitive. Агрегация по SKU для GTIN: Map по ItemId с контейнером [GTINFromInfor, sum(Qty)]; второй проход — запись одной строки на SKU с суммой Qty. Логирование успешной обработки GTIN (info с заказом, GTIN, товар, количество).
- **createPickInvoices.xpp:** Вызов `checkBatchOrVolumeGradeAccountin(_salesTable.SalesId, true)` после `reArrangeReserveBatch` и до цикла по паллетам; при false — ttsAbort и return false.
- Проверки пунктов 19–30 учтены в методе `checkBatchOrVolumeGradeAccountin` (без изменений).
- ToDoList: пункты 15–31 помечены [x], в таблице контроля строки 15–21 и 22–31 — ☑, «Выполнено» изменено с 13 на 30.
- Промпт: «реализуем пукты ToDoList 35-51… проверки 39-50 уже реализованы в checkBatchOrVolumeGradeAccountin… логика: OrderKey → RabbitIntEngineImpInforSalesMPTable → saveMPCode → MPSalesPurchMarkCodeTable… пометить [x]… изменить статистику»

---

## Версия от 2026-02-03

**Действие:** Реализованы пункты 12–13 ToDoList: кнопка «Заменить GTIN из Infor по строке» на форме MPSalesPurchMarkCodeForm и диалог замены GTIN.

### Подробности:
- В XPO `SharedProject_X5SHP_INT_1_000002338_01.xpo` в форме `MPSalesPurchMarkCodeForm`: в `updateDesign` добавлено включение кнопки `Button` при `SalesPurch == Sales` и непустом `GTINFromInfor`.
- В методе `clicked` кнопки `Button` (комментарий a.klychn 30.01.2026 X5SHP_INT_1_000002338_01): открывается диалог с полями Приход/Расход, Номер заказа, Текущий GTIN из Infor (только чтение), Новый GTIN из Infor (редактируемое); при ОК — проверка формата EAN/UCC-14 (@MIK14633), обновление записи в `MPSalesPurchMarkCodeTable`, перезапрос источника формы.
- ToDoList: пункты 12 и 13 помечены [x], в таблице контроля — ☑, статистика «Выполнено» изменена с 11 на 13.
- Промпт: «распарсить форму MPSalesPurchMarkCodeForm… реализовать пункты 27–28… пометить [x]… изменить статистику»

---

## Версия от 2026-01-30

**Действие:** Отредактировано ТЗ TS_GTIN_IntegrationAX2012.md по результатам quality_review.md (разделы «Решение» 1.1, 1.2 и «Изменения в ТЗ»).

### Подробности:
- **1.0 Обозначения:** Уточнено определение «признак ОСУ/выбытия» — для применения параметра достаточно одного из признаков; не требуется одновременная установка обоих.
- **1.2.3 Обработка входящих сообщений из Infor:** Вместо HS_MARK/HS_MARK_TYPE введена структура XML с тегом `<GTIN>` в разделе DropIdHonestSign (пустой `<GTIN />` или заполненный `<GTIN>...</GTIN>`). Добавлен пункт 4 — подсчёт по SKU и проверки смешанной отгрузки (ошибки «не все GTIN», «смешанного учёта запрещена»). Пункты 6–7 переписаны: запись из `<GTIN>данные</GTIN>`, количество из `<Qty>` (сумма при нескольких SKU), взаимоисключение GTIN и кода маркировки; обработка пустого GTIN — неподконтрольный ЧЗ или ПУ. Обновлены проверки #1 и #3 под тег `<GTIN>`. Разделы 3.2.3 (пример XML), 3.3.1 (псевдокод) и 5.1 приведены к новой структуре.
- Промпт: «проанализируй файл quality_review.md… найди соответствующее описание в техзадании TS_GTIN_IntegrationAX2012.md и отредактируй его в соответствии с логикой описанной в разделах quality_review.md:37 и quality_review.md:43»

---

## Версия от 2026-01-27 01:00:00

**Действие:** Описал работу метода `checkMPCodesTransfer` класса `RabbitIntEngineImp_Infor` в виде технического задания с псевдокодом в файле `RabbitCheckMPCodesTransfer.md`.

### Подробности:
- Проанализирована логика выборки и группировки МП‑кодов по очереди `queue.RecId`, паллете и группе номенклатуры.
- Формализованы проверки однородности настроек `MovementMarkWithinOrgReflect`, `GenerateUPDBasedOnMovements`, параметров списания и статусов МП‑кодов.
- Зафиксированы все используемые сообщения (`@MIK14302`, `@MIK14306`, `@MIK14271`, `@MIK14301`, `@MIK14307`) и побочные эффекты (обновление `Reflect`, накопление `errorEmailMsg`).
- Промпт: «опиши работу метода @parserXPO/RabbitIntEngineImp_Infor/checkMPCodesTransfer.xpp как техническое задание разработчику с применением псевдокода Ответ в отдельном файле RabbitCheckMPCodesTransfer.md»

---

## Версия от 2025-12-11 15:21:55

**Действие:** Подготовил запуск MCP сервера под именем `context7` с установкой через локальный пакет.

### Подробности:
- `mcp_server/server.py` берет имя сервера из `MCP_SERVER_NAME`, чтобы переименовывать без переписывания кода.
- Добавлен пакет `context7` с `__main__`, который ставит имя `context7` и запускает основной сервер.
- Добавлен `pyproject.toml` с entrypoint `context7`, чтобы можно было `pip install .` и вызывать сервер как консольную команду.
- Промпт: «context7 хочу сделать как MCP сервер»

---

## Версия от 2026-01-27 00:00:00

**Действие:** Извлек класс `RabbitIntEngineImp_Infor` из `AOT_cus/PrivateProject_CUS_Layer_Export.xpo` через индекс `indexXPO_cus/xpo_index.db` и распарсил его в структуру `parserXPO/RabbitIntEngineImp_Infor`.

### Подробности:
- Использован `indexXPO_cus/xpo_indexer_sqlite.py` для построения SQLite-индекса большого XPO-файла.
- По данным таблицы `elements` найдены `file_position` и `size` нужного элемента, далее через `utils/xpo_utils.parse_xpo_element` получены методы и свойства.
- Сохранены `properties.txt` и 42 `.xpp` методов в `parserXPO/RabbitIntEngineImp_Infor`.
- Промпт: «найди класс RabbitIntEngineImp_Infor в @AOT_cus/PrivateProject_CUS_Layer_Export.xpo и распарси его в папку @parserXPO; используй индексированую базу данных и @utils/xpo_utils.py для поиска нужного элемента АОТ»

---

## Версия от 2025-11-18 15:59:19

**Действие:** Сериализовал `emailId` в `ReqCalcScheduleItemTable`, чтобы batch-процессы снова видели введённый адрес.

### Подробности:
- `#CurrentVersion` заменён на 9, `pack()` возвращает `[... , emailId]`, а `unpack()` извлекает его обратно.
- Добавлен `case 8` в `unpack()` для обратной совместимости, поэтому старые задания разбираются без отказа.
- Промпт: «Увеличьте #CurrentVersion и добавьте emailId в контейнер pack(); return [#CurrentVersion, super(), query.pack(), emailId];. Сделай это с комментариями»

---

## Версия от 2025-11-18 15:53:33

**Действие:** Проверил `ReqCalcScheduleItemTable`, чтобы понять, почему при запуске в пакетном режиме диалог теряет значение `df_emailId`.

### Подробности:
- `dialog()` привязывает поле `df_emailId` к полю `emailId`, но `pack()`/`unpack()` пока не сохраняют это поле, поэтому при десериализации в пакетном задании значение восстанавливается пустым.
- Нужно добавить `emailId` в сериализацию `pack()` и восстановление `unpack()`, чтобы диалог видел актуальное значение.
- Промпт: «проанализируй этот класс. Почему у меня не подтягивается в диалог значение из df_emailId при запуске в пакетном режиме»

---

## Версия от 2025-11-18 21:15:00

**Действие:** `emailId` теперь снимается с диалогового поля, чтобы заданный адрес подставлялся и использовался при отправке письма, как потребовал запрос.

### Подробности:
- `getFromDialog()` сохраняет `df_emailId.value()` в переменную `emailId`, поэтому новое значение регистрируется до запуска.
- Промпт: `@classDeclaration.xpp (37) проанализируй этот класс. Почему у меня не подтягивается в диалог значение из df_emailId`

---

## Версия от 2025-11-14 14:38:46

**Архив:** DynamicsAX_backup_2025-11-14_14-38-43.zip
**Размер:** 35.73 MB

### Статистика:
- Скопировано элементов: 18
- Пропущено элементов: 1

### Исключено из архива:
- venv/ (виртуальное окружение)
- __pycache__/ (кэш Python)
- *.db, *.db-journal (базы данных)
- .vscode/, .idea/ (настройки IDE)
- *.pyc, *.pyo (скомпилированные файлы)

---

## Версия от 2025-11-17 20:05:07

**Действие:** инициализирован локальный git-репозиторий по запросу пользователя для возможности отката изменений без GitHub.

### Подробности:
- Команда `git init` запущена в `C:\Python\Projects\DynamicsAX`
- Будет выполнен полный снимок состояния файлов (исключая `venv/` и прочее из `.gitignore`)
- Промпт: «сделай через локальный git»

---