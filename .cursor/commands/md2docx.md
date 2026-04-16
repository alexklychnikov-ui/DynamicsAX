# Markdown → DOCX (md2docx)

Конвертация `.md` в `.docx` с нормальной вёрсткой: шрифты, поля, оглавление, таблицы (рамки, заливка шапки, повтор шапки на новой странице), блоки кода.

**Рабочая директория:** корень репозитория `DynamicsAX`.

**Зависимости:** [Pandoc](https://pandoc.org/installing.html) в PATH; в выбранном Python — пакет `python-docx` (`pip install python-docx` или из корня: `pip install -r requirements.txt`).

**Запуск с приоритетом venv в корне проекта** (`venv` или `.venv`), иначе `python` из PATH:

```powershell
Set-Location "<корень_DynamicsAX>"
$pyCandidates = @(
  (Join-Path (Get-Location) 'venv\Scripts\python.exe'),
  (Join-Path (Get-Location) '.venv\Scripts\python.exe')
)
$python = $pyCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python) {
  $python = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
}
if (-not $python) { throw 'Python не найден (создайте venv в корне или добавьте python в PATH).' }
& $python (Join-Path (Get-Location) 'md2docx.py') '<путь_к_файлу.md>'
```

Пример (относительный путь от корня):

```powershell
Set-Location "c:\Python\Projects\DynamicsAX"
$python = @(
  (Join-Path (Get-Location) 'venv\Scripts\python.exe'),
  (Join-Path (Get-Location) '.venv\Scripts\python.exe')
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python) { $python = 'python' }
& $python (Join-Path (Get-Location) 'md2docx.py') 'Projects\Rabbit\Documentation\RabbitIntNewAlgoritm.md'
```

Свой путь к `.docx`:

```text
python md2docx.py "path\to\file.md" -o "path\to\out.docx"
```

Скрипт печатает абсолютный путь к созданному файлу. Кратко сообщи путь к `.docx` и что исходный `.md` обработан без ошибок.
