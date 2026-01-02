#!/usr/bin/env python3
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Выполнить команду и обработать ошибки"""
    print(f"🔧 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} выполнено успешно")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при выполнении: {description}")
        print(f"   Команда: {cmd}")
        print(f"   Код ошибки: {e.returncode}")
        sys.exit(1)

def check_linux():
    """Проверить, что система Linux"""
    if sys.platform != "linux":
        print("❌ Эта программа работает только на Linux")
        print(f"   Текущая ОС: {sys.platform}")
        sys.exit(1)

def download_scripty():
    """Скачать scripty с GitHub Releases"""
    github_tag = "v1.0.0-dev"
    download_url = f"https://github.com/stastpru/scripty/releases/download/{github_tag}/scripty"
    
    try:
        print(f"📥 Скачивание scripty (версия: {github_tag})...")
        
        # Пытаемся использовать requests, если доступен
        try:
            import requests
            file_response = requests.get(download_url)
            file_response.raise_for_status()
            
            with open("scripty", "wb") as f:
                f.write(file_response.content)
                
        except ImportError:
            # Альтернатива через curl, если requests не установлен
            print("   Библиотека requests не найдена, использую curl...")
            run_command(f"curl -L -o scripty {download_url}", 
                       f"Скачивание через curl")
        
        print(f"✅ Файл 'scripty' версии {github_tag} успешно скачан")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при скачивании: {e}")
        print(f"   URL: {download_url}")
        return False

def main():
    # Проверка операционной системы
    check_linux()
    
    # Получаем домашнюю директорию
    home_dir = Path.home()
    script_dir = Path(__file__).parent.absolute()
    
    # 0. Скачиваем scripty, если его нет
    source_script = script_dir / "scripty"
    
    if not source_script.exists():
        print("📦 Файл 'scripty' не найден, пытаемся скачать...")
        if not download_scripty():
            print("❌ Не удалось скачать scripty. Установка прервана.")
            sys.exit(1)
    else:
        print("✅ Файл 'scripty' уже существует, пропускаем скачивание")
    
    # 1. Копирование scripty в /usr/bin/scripty
    
    # Проверяем существует ли исходный файл
    if not source_script.exists():
        print("❌ Файл 'scripty' не найден в текущей директории")
        sys.exit(1)
    
    run_command(f"sudo cp {source_script} /usr/bin/scripty", 
                "Копирование scripty в /usr/bin/")
    
    # 2. Установка прав выполнения
    run_command("sudo chmod +x /usr/bin/scripty", 
                "Установка прав выполнения для scripty")
    
    # 3. Создание директорий
    scripty_home = home_dir / ".scripty"
    modules_dir = scripty_home / "modules"
    templates_dir = scripty_home / "templates"
    
    print(f"🔧 Создание структуры директорий в {scripty_home}...")
    
    try:
        modules_dir.mkdir(parents=True, exist_ok=True)
        templates_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Директории созданы успешно")
    except Exception as e:
        print(f"❌ Ошибка при создании директорий: {e}")
        sys.exit(1)
    
    # 4. Создание файла шаблона
    template_file = templates_dir / "python.simple.json"
    template_data = {
        "actions": {
            "install": "pip install -r requirements.txt"
        }
    }
    
    print(f"🔧 Создание файла шаблона {template_file}...")
    
    try:
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=4, ensure_ascii=False)
        print("✅ Файл шаблона создан успешно")
    except Exception as e:
        print(f"❌ Ошибка при создании файла шаблона: {e}")
        sys.exit(1)
    
    # Проверяем, что все создалось правильно
    print("\n" + "="*50)
    print("📋 Проверка установки:")
    print("="*50)
    
    # Проверка файла scripty
    if Path("/usr/bin/scripty").exists():
        print("✅ /usr/bin/scripty - существует")
        # Проверяем права доступа
        stat = os.stat("/usr/bin/scripty")
        if stat.st_mode & 0o111:
            print("✅ /usr/bin/scripty - права на выполнение установлены")
        else:
            print("⚠️  /usr/bin/scripty - права на выполнение НЕ установлены")
    else:
        print("❌ /usr/bin/scripty - не найден")
    
    # Проверка директорий
    if scripty_home.exists():
        print(f"✅ {scripty_home} - существует")
    else:
        print(f"❌ {scripty_home} - не найден")
    
    if modules_dir.exists():
        print(f"✅ {modules_dir} - существует")
    else:
        print(f"❌ {modules_dir} - не найден")
    
    if templates_dir.exists():
        print(f"✅ {templates_dir} - существует")
    else:
        print(f"❌ {templates_dir} - не найден")
    
    if template_file.exists():
        print(f"✅ {template_file} - существует")
        
        # Проверяем содержимое файла
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "actions" in data and "install" in data["actions"]:
                print("✅ Структура JSON файла корректна")
            else:
                print("⚠️  Структура JSON файла отличается от ожидаемой")
        except json.JSONDecodeError:
            print("❌ Ошибка в формате JSON файла")
    else:
        print(f"❌ {template_file} - не найден")
    
    print("\n" + "="*50)
    print("🎉 Установка завершена успешно!")
    print(f"Установлена версия: v1.0.0-dev")
    print("Вы можете использовать команду 'scripty' в терминале")
    print("="*50)

if __name__ == "__main__":
    # Проверка прав суперпользователя
    if os.geteuid() != 0:
        print("⚠️  Для установки в /usr/bin/ требуются права суперпользователя")
        print("   Программа запросит пароль sudo при необходимости")
        print()
    
    main()