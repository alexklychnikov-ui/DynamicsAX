import re
import sys
from pathlib import Path
from typing import Iterable


# Типичные "плохие" символы, появляющиеся при битой перекодировке
BAD_CHARS = ('Р', 'С', 'Ð', 'Ñ')

# Очень упрощённый регекс для строковых литералов
STRING_RE = re.compile(r'(["\'])(?:\\.|(?!\1).)*\1')


def has_mojibake(s: str) -> bool:
    return any(ch in s for ch in BAD_CHARS)


def clean_string_literals(line: str) -> str:
    """
    Если в строковом литерале есть кракозябры — заменяем его на короткий текст.
    Остальная часть строки (print/raise/format и т.п.) не трогаем.
    """

    def repl(m: re.Match) -> str:  # type: ignore[name-defined]
        text = m.group(0)
        if not has_mojibake(text):
            return text

        quote = text[0]
        new_inner = "[text removed due to encoding error]"
        return f"{quote}{new_inner}{quote}"

    return STRING_RE.sub(repl, line)


def clean_comment(line: str) -> str:
    """
    Если после # есть кракозябры — заменяем комментарий на короткий.
    """
    if '#' not in line:
        return line

    before, comment = line.split('#', 1)
    if not has_mojibake(comment):
        return line

    return f"{before}# [removed corrupted comment]\n"


def clean_plain_mojibake(line: str) -> str:
    """
    Строки без кавычек/комментариев, но с кракозябрами (обычно текст docstring’ов):
    заменяем на короткий комментарий.
    """
    if not has_mojibake(line):
        return line

    if ('"' in line) or ("'" in line) or ('#' in line):
        return line

    indent = len(line) - len(line.lstrip(' '))
    return ' ' * indent + '# [removed corrupted text]\n'


def process_lines(lines: Iterable[str]) -> Iterable[str]:
    for line in lines:
        if not has_mojibake(line):
            yield line
            continue

        line = clean_comment(line)
        line = clean_string_literals(line)

        if has_mojibake(line):
            line = clean_plain_mojibake(line)

        if not line.strip():
            line = "# [line cleaned and became empty]\n"

        yield line


def clean_file(path: Path, backup: bool = True) -> None:
    print(f"Cleaning mojibake in: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)

    new_lines = list(process_lines(lines))

    if backup:
        backup_path = path.with_suffix(path.suffix + ".bak")
        backup_path.write_text(text, encoding="utf-8", errors="ignore")
        print(f"  Backup saved to: {backup_path}")

    path.write_text("".join(new_lines), encoding="utf-8", errors="ignore")
    print("  Done\n")


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        print("Usage: python fix_mojibake.py xpo_writer.py [other_files.py ...]")
        print("WARNING: script is destructive; it overwrites files in place.")
        return

    for name in argv[1:]:
        p = Path(name)
        if not p.is_file():
            print(f"Skip (not a file): {p}")
            continue
        clean_file(p)


if __name__ == "__main__":
    main(sys.argv)

