import argparse
import yaml
import json
import os
from pathlib import Path
import sys
import importlib.util
from typing import Dict, Any, List, Optional

base_dir=["~/.scripty", ".scripty"]

parser = argparse.ArgumentParser(description='Scrypty')
parser.add_argument('command', nargs='*', help='команда')
args = parser.parse_args()

class ScriptyModule:
    """Базовый класс для модулей Scripty"""
    __prefix__: str = ""

def load_config():
    if os.path.exists("scripty.yaml"):
        with open('scripty.yaml', 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return data
    else:
        return None
    
def get_arg(index, default, args):
    try:
        return args.command[index]
    except IndexError:
        return default

def get_json_file(filename):
    for directory in base_dir:
        file_path = Path(directory) / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return False

def load_module_from_path(module_path: Path) -> Any:
    """Загружает модуль из файла"""
    try:
        module_name = f"scripty_module_{module_path.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        spec.loader.exec_module(module)
        
        return module
    except Exception as e:
        print(f"Ошибка загрузки модуля {module_path}: {e}")
        return None

def validate_module(module: Any) -> bool:
    """Проверяет, что модуль валиден"""
    try:
        if not hasattr(module, 'ScriptyModule'):
            return False
            
        scripty_class = module.ScriptyModule
        if not hasattr(scripty_class, '__prefix__') or not scripty_class.__prefix__:
            return False
            
        return True
    except Exception:
        return False

def get_module_instance(module: Any) -> ScriptyModule:
    """Создает экземпляр класса модуля"""
    return module.ScriptyModule()

def discover_modules(basedirs: List[str]) -> Dict[str, Any]:
    """
    Обнаруживает и загружает модули из указанных директорий
    
    Args:
        basedirs: Список базовых директорий (чем дальше, тем приоритетнее)
    
    Returns:
        Словарь {prefix: module_object}
    """
    modules: Dict[str, Any] = {}
    
    for basedir in reversed(basedirs):
        expanded_dir = os.path.expanduser(basedir)
        modules_dir = Path(expanded_dir) / "modules"
        
        if not modules_dir.exists():
            continue

        for py_file in modules_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
                
            print(f"Загрузка модуля: {py_file}")
            module = load_module_from_path(py_file)
            
            if module is None or not validate_module(module):
                print(f"Модуль {py_file} не прошел валидацию")
                continue

            prefix = module.ScriptyModule.__prefix__

            modules[prefix] = get_module_instance(module)
    
    return modules

config = load_config()

if config is None:
    if not args.command or args.command[0] != "init":
        print("Конфиг не существует. Пожалуйста, убедитесь что вы в папке проекта или создайте конфиг используя 'init'")
        sys.exit(1)

if not args.command:
    print("Не указана команда")
    sys.exit(1)

command = args.command[0]

if command == "init":
    if config:
        print("Конфиг уже существует")
        sys.exit(2)
    
    template = get_arg(1, "python.simple", args)
    if os.path.exists("scripty.yaml"):
        print("Конфиг уже существует")
        sys.exit(2)
    
    config_data = get_json_file(f"templates/{template}.json") 
    if config_data == False:
        print("Шаблон не найден")
        sys.exit(2)
    
    config_data["name"] = input("Имя проекта: ") or "Проект"
    config_data["version"] = input("Версия: ") or "v1.0.0"
    try:
        with open("scripty.yaml", 'w', encoding='utf-8') as yaml_file:
            import yaml
            yaml.dump(config_data, yaml_file, default_flow_style=False, allow_unicode=True)
        print("Конфиг scripty.yaml успешно создан")
        sys.exit(0)
    except Exception as e:
        print(f"Ошибка при записи конфига: {e}")
        sys.exit(1)

if command == "help":
    print("Основные команды:")
    print("init [template] - Инициализировать проект из примеров")
    print("run <action> - Запуск действия из scripty.yaml")
    print("modules list - модули(функционал в разработке, но работает)")
    sys.exit(0)

if not config:
    print("Конфиг не существует")
    sys.exit(2)

if command == "run":
    arg = f"{get_arg(1, '', args)} {get_arg(2, '', args)} {get_arg(3, '', args)} {get_arg(4, '', args)}".strip() # инжинеры ненавидят простые решения
    
    actions = config.get("actions")
    if not actions:
        print("Ошибка: секция 'actions' не найдена в конфигурации")
        sys.exit(1)
    
    cmd = actions.get(arg)
    if not cmd:
        print(f"Ошибка: действие '{arg}' не найдено в конфигурации")
        print(f"Доступные действия: {', '.join(actions.keys())}")
        sys.exit(1)
    
    try:
        if(isinstance(cmd, str)):
            print(f"Выполняется: {cmd}")

            exit_code = os.system(cmd)

            if exit_code != 0:
                print(f"Команда завершилась с кодом ошибки {exit_code}")
        elif(isinstance(cmd, list)):
            from datetime import datetime

            start_total = datetime.now()

            for idx, i in enumerate(cmd, 1):
                print(f" → Шаг {idx}/{len(cmd)}: {i}")

                step_start = datetime.now()
                exit_code = os.system(i)
                step_time = datetime.now() - step_start

                # Форматируем дельту времени
                total_seconds = step_time.total_seconds()

                if total_seconds < 60:
                    time_display = f"{total_seconds:.1f} секунд"
                else:
                    minutes = int(total_seconds // 60)
                    seconds = int(total_seconds % 60)
                    time_display = f"{minutes} мин {seconds} сек"

                if exit_code != 0:
                    print(f"✗ Шаг {idx} завершился с ошибкой [{time_display}]")
                    print(f"   Код ошибки: {exit_code}")
                    sys.exit(2)
                else:
                    print(f"✓ Шаг {idx} выполнен успешно [{time_display}]")

            total_time = datetime.now() - start_total
            total_seconds = total_time.total_seconds()

            if total_seconds < 60:
                total_display = f"{total_seconds:.1f} секунд"
            else:
                minutes = int(total_seconds // 60)
                seconds = int(total_seconds % 60)
                total_display = f"{minutes} мин {seconds} сек"

            print(f"\nВсе операции завершены за {total_display}")
    except Exception as e:
        print(f"Ошибка при выполнении команды: {e}")
    sys.exit(0)

modules = discover_modules(base_dir)

if command == "modules":
    subcmd = get_arg(1, "list", args)
    if subcmd == "list":
        print(f"\nЗагружено модулей: {len(modules)}")
        for prefix, module in modules.items():
            print(f" - {prefix}: {type(module).__name__}")
    sys.exit(0)

if modules.get(command):
    modules[command].run(args, config)
    sys.exit(0)

print("Команда не найдена!")