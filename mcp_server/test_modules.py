#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки модулей MCP сервера
"""
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from label_loader import LabelLoader
from xpo_reader import XPOReader
from parser_integration import ParserIntegration

PROJECT_ROOT = Path(__file__).parent.parent
XPO_FILE = PROJECT_ROOT / "AOT_cus" / "PrivateProject_CUS_Layer_Export.xpo"
ALD_FILE = PROJECT_ROOT / "AOT_cus" / "AxMIKru.ald"
DB_FILE = PROJECT_ROOT / "indexXPO_cus" / "xpo_index.db"
PARSER_DIR = PROJECT_ROOT / "parserXPO"


def test_label_loader():
    """Тестирует загрузку меток"""
    print("Тест 1: Загрузка меток из ALD файла...")
    try:
        loader = LabelLoader(str(ALD_FILE))
        print(f"  Загружено меток: {len(loader.get_all_labels())}")
        
        # Тест получения метки
        label = loader.get_label("MIK9")
        if label:
            print(f"  МИК9: {label[:50]}...")
        else:
            print("  МИК9 не найдена")
        
        # Тест поиска меток в тексте
        test_text = "Label #@MIK9 и еще @MIK10"
        found = loader.find_labels_in_text(test_text)
        print(f"  Найдено меток в тестовом тексте: {len(found)}")
        
        print("  [OK] LabelLoader работает корректно\n")
        return True
    except Exception as e:
        print(f"  [ERROR] Ошибка: {e}\n")
        return False


def test_xpo_reader():
    """Тестирует чтение XPO файла"""
    print("Тест 2: Чтение XPO файла...")
    try:
        reader = XPOReader(str(XPO_FILE), str(DB_FILE))
        
        # Тест поиска элемента
        element = reader.find_element("Global", "CLS")
        if element:
            print(f"  Найден элемент: {element['element_name']} ({element['element_type']})")
            
            # Тест получения методов
            methods = reader.get_element_methods(element['id'])
            print(f"  Методов в элементе: {len(methods)}")
            
            # Тест получения кода метода
            if methods:
                method_code = reader.get_method_code("Global", methods[0], "CLS")
                if method_code:
                    print(f"  Код метода '{methods[0]}': {len(method_code)} символов")
        else:
            print("  Элемент Global не найден")
        
        # Тест полнотекстового поиска
        results = reader.fulltext_search("Global", "CLS", limit=5)
        print(f"  Результатов поиска 'Global': {len(results)}")
        
        reader.close()
        print("  [OK] XPOReader работает корректно\n")
        return True
    except Exception as e:
        print(f"  [ERROR] Ошибка: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_parser_integration():
    """Тестирует интеграцию с parserXPO"""
    print("Тест 3: Интеграция с parserXPO...")
    try:
        integration = ParserIntegration(str(PARSER_DIR))
        
        # Проверяем существование элемента
        exists = integration.element_exists("Global")
        print(f"  Элемент Global существует: {exists}")
        
        if exists:
            # Читаем методы
            methods = integration.read_element_methods("Global")
            print(f"  Методов в parserXPO/Global: {len(methods)}")
            
            if methods:
                # Читаем один метод
                first_method = list(methods.keys())[0]
                code = integration.read_method("Global", first_method)
                if code:
                    print(f"  Метод '{first_method}': {len(code)} символов")
        
        print("  [OK] ParserIntegration работает корректно\n")
        return True
    except Exception as e:
        print(f"  [ERROR] Ошибка: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_label_usage():
    """Тестирует поиск использования меток"""
    print("Тест 4: Поиск использования меток...")
    try:
        reader = XPOReader(str(XPO_FILE), str(DB_FILE))
        
        # Ищем использование метки MIK9
        results = reader.find_label_usage("MIK9")
        print(f"  Найдено использований метки MIK9: {len(results)}")
        
        if results:
            for result in results[:3]:  # Показываем первые 3
                print(f"    {result['element_type']} {result['element_name']}: {len(result['methods'])} методов")
        
        reader.close()
        print("  [OK] Поиск использования меток работает корректно\n")
        return True
    except Exception as e:
        print(f"  [ERROR] Ошибка: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование модулей MCP сервера")
    print("=" * 60)
    print()
    
    results = []
    results.append(test_label_loader())
    results.append(test_xpo_reader())
    results.append(test_parser_integration())
    results.append(test_label_usage())
    
    print("=" * 60)
    print(f"Результаты: {sum(results)}/{len(results)} тестов пройдено")
    print("=" * 60)

