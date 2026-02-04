#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки рефакторинга
"""
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_utils():
    """Тестирует модуль utils"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ utils/xpo_utils.py")
    print("=" * 60)
    
    from utils.xpo_utils import (
        clean_xpo_code,
        format_code_for_xpo,
        extract_element_name,
        extract_methods,
        extract_properties,
        find_labels_in_text,
        ELEMENT_PATTERNS,
    )
    
    # Тест clean_xpo_code
    test_code = """\t#def testMethod(arg1, arg2):
\t#    # Тестовый код
\t#    return arg1 + arg2"""
    cleaned = clean_xpo_code(test_code)
    print(f"\n[clean_xpo_code] Исходный код очищен: {len(cleaned)} символов")
    
    # Тест format_code_for_xpo
    formatted = format_code_for_xpo("return arg1 + arg2", indent='    ')
    assert formatted.startswith('    #'), "Форматирование не работает"
    print("[format_code_for_xpo] Код отформатирован для XPO")
    
    # Тест extract_element_name
    cls_content = "CLASS #TestClass\nPROPERTIES\nENDPROPERTIES"
    name = extract_element_name('CLS', cls_content)
    assert name == "TestClass", f"Ожидалось 'TestClass', получено '{name}'"
    print("[extract_element_name] Имя класса извлечено")
    
    # Тест find_labels_in_text
    text_with_labels = "info(strfmt(\"@MIK123\", value)); // Comment @MIK456"
    labels = find_labels_in_text(text_with_labels)
    assert '123' in labels and '456' in labels, "Метки не найдены"
    print(f"[find_labels_in_text] Найдено меток: {len(labels)}")
    
    print("\n✓ Все тесты utils пройдены успешно!")
    return True


def test_xpo_parser():
    """Тестирует xpo_parser.py"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ xpo_parser.py")
    print("=" * 60)
    
    from xpo_parser import XPOParser
    
    # Создаем тестовый контент
    test_xpo = """***Element: CLS
CLASS #TestClass
PROPERTIES
    Extends    #xRecord
ENDPROPERTIES
METHODS
SOURCE #new
    #public void new()
    #{
    #    super();
    #}
ENDSOURCE
SOURCE #testMethod
    #public void testMethod()
    #{
    #    print("Hello");
    #}
ENDSOURCE
ENDMETHODS
"""
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xpo', delete=False) as f:
        f.write(test_xpo)
        temp_path = f.name
    
    try:
        parser = XPOParser(temp_path)
        parser.parse()
        
        assert 'TestClass' in parser.objects, "Класс не найден"
        assert parser.objects['TestClass']['type'] == 'CLS', "Тип элемента неверный"
        assert 'new' in parser.objects['TestClass']['methods'], "Метод new не найден"
        assert 'testMethod' in parser.objects['TestClass']['methods'], "Метод testMethod не найден"
        
        # Проверяем, что Extends извлечен
        assert parser.objects['TestClass']['properties'].get('extends') == 'xRecord', \
            "Extends не извлечен правильно"
        
        print("[XPOParser] Парсинг элементов работает")
        print(f"[XPOParser] Найдено объектов: {len(parser.objects)}")
        
        print("\n✓ Все тесты xpo_parser пройдены успешно!")
        return True
    finally:
        os.unlink(temp_path)


def test_xpo_writer():
    """Тестирует xpo_writer.py"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ xpo_writer.py")
    print("=" * 60)
    
    import tempfile
    import os

    from xpo_writer import XPOWriter
    
    test_xpo = """***Element: CLS
CLASS #TestClass
PROPERTIES
ENDPROPERTIES
METHODS
SOURCE #new
    #public void new()
    #{
    #    super();
    #}
ENDSOURCE
ENDMETHODS
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xpo', delete=False) as f:
        f.write(test_xpo)
        temp_path = f.name
    
    try:
        writer = XPOWriter(temp_path)
        
        # Тест форматирования метода
        method_code = """public void new()
{
    super();
}"""
        formatted = writer._format_code_for_xpo(method_code)
        assert '    #' in formatted, "Форматирование не добавило префиксы"
        print("[XPOWriter] Форматирование методов работает")
        
        print("\n✓ Все тесты xpo_writer пройдены успешно!")
        return True
    finally:
        os.unlink(temp_path)


def main():
    """Запускает все тесты"""
    print("\n" + "=" * 60)
    print("РЕФАКТОРИНГ - ТЕСТИРОВАНИЕ")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_utils()
    except Exception as e:
        print(f"\n✗ Ошибка в test_utils: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        all_passed &= test_xpo_parser()
    except Exception as e:
        print(f"\n✗ Ошибка в test_xpo_parser: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        all_passed &= test_xpo_writer()
    except Exception as e:
        print(f"\n✗ Ошибка в test_xpo_writer: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("=" * 60)
        return 0
    else:
        print("✗ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())