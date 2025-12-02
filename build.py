#!/usr/bin/env python3
"""
Скрипт сборки УВМ для всех платформ (Windows, Linux, Web)
Без TUI версии (uvm_tui.py исключен)
"""

import os
import sys
import shutil
import platform
import subprocess
import zipfile
import tarfile
from pathlib import Path

class UVMBuilder:
    """Класс для сборки УВМ на разных платформах"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        
        # Файлы проекта (БЕЗ uvm_tui.py)
        self.core_files = [
            "uvm_asm.py",
            "uvm_interp.py", 
            "uvm_gui.py",
            "README.txt",
            "QUICKSTART.txt"
        ]
        
        # Примеры программ (добавляем те, что создали)
        self.example_files = [
            "test_spec_format.uvm",
            "task_vector_max.uvm",
            "example1_find_max.uvm",
            "example2_matrix.uvm",
            "example3_time_series.uvm",
            "test_stage5.py",
            "test_array_copy.uvm",
            "test_max.uvm",
            "test_vectors.uvm"
        ]
        
        # Опциональные файлы (если существуют)
        self.optional_files = [
            "requirements.txt",
            "run_stage5.bat",
            "test_commands.py"
        ]
    
    def clean(self):
        """Очистка директорий сборки"""
        print("🧹 Очистка директорий сборки...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  Удалено: {dir_path}")
        
        # Создаем чистые директории
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        print("✅ Очистка завершена")
    
    def copy_project_files(self):
        """Копирование основных файлов проекта"""
        print("📋 Копирование файлов проекта...")
        
        copied_count = 0
        for file_name in self.core_files:
            src = self.project_root / file_name
            if src.exists():
                dst = self.build_dir / file_name
                shutil.copy2(src, dst)
                print(f"  ✓ {file_name}")
                copied_count += 1
            else:
                print(f"  ⚠  Не найден: {file_name}")
        
        # Копируем опциональные файлы
        for file_name in self.optional_files:
            src = self.project_root / file_name
            if src.exists():
                dst = self.build_dir / file_name
                shutil.copy2(src, dst)
                print(f"  ⚙  {file_name} (опциональный)")
        
        print(f"✅ Скопировано {copied_count} основных файлов")
    
    def copy_examples(self):
        """Копирование примеров программ"""
        print("📝 Копирование примеров программ...")
        
        examples_dir = self.build_dir / "examples"
        examples_dir.mkdir(exist_ok=True)
        
        copied_count = 0
        for example in self.example_files:
            src = self.project_root / example
            if src.exists():
                dst = examples_dir / example
                shutil.copy2(src, dst)
                print(f"  📄 {example}")
                copied_count += 1
            else:
                # Пробуем найти в других местах
                possible_paths = [
                    self.project_root / "test_programs" / example,
                    self.project_root / "tests" / example,
                    self.project_root / "samples" / example
                ]
                for path in possible_paths:
                    if path.exists():
                        dst = examples_dir / example
                        shutil.copy2(path, dst)
                        print(f"  📄 {example} (из {path.parent.name}/)")
                        copied_count += 1
                        break
        
        if copied_count == 0:
            print("  ⚠  Примеры не найдены, создаем базовые...")
            self.create_basic_examples(examples_dir)
            copied_count = len(self.example_files)
        
        print(f"✅ Скопировано {copied_count} примеров")
    
    def create_basic_examples(self, examples_dir):
        """Создание базовых примеров если их нет"""
        basic_example = """# Базовый пример УВМ
{"op": "load_const", "address": 100, "constant": 42}
{"op": "read", "dst_addr": 200, "src_addr": 100}
{"op": "write", "src_addr": 200, "offset": 5, "base_addr": 300}
{"op": "max", "addr_b": 100, "addr_c": 400, "addr_d": 200}"""
        
        with open(examples_dir / "basic_example.uvm", 'w', encoding='utf-8') as f:
            f.write(basic_example)
        
        spec_example = """# Тесты из спецификации
{"op": "load_const", "address": 825, "constant": 559}
{"op": "read", "dst_addr": 84, "src_addr": 215}
{"op": "write", "src_addr": 193, "offset": 30, "base_addr": 352}
{"op": "max", "addr_b": 782, "addr_c": 367, "addr_d": 565}"""
        
        with open(examples_dir / "spec_tests.uvm", 'w', encoding='utf-8') as f:
            f.write(spec_example)
    
    def build_windows(self):
        """Сборка для Windows"""
        print("\n🪟 Сборка для Windows...")
        
        windows_dir = self.dist_dir / "windows"
        windows_dir.mkdir(exist_ok=True)
        
        # Копируем основные файлы
        for file_name in self.core_files:
            src = self.build_dir / file_name
            if src.exists():
                dst = windows_dir / file_name
                shutil.copy2(src, dst)
        
        # Копируем примеры
        if (self.build_dir / "examples").exists():
            windows_examples = windows_dir / "examples"
            shutil.copytree(self.build_dir / "examples", windows_examples, dirs_exist_ok=True)
        
        # Создаем bat-файлы для запуска
        self.create_windows_scripts(windows_dir)
        
        # Создаем архив ZIP
        archive_path = self.dist_dir / "uvm_windows"
        self.create_zip_archive(windows_dir, archive_path)
        
        print(f"✅ Сборка для Windows завершена")
        print(f"   📦 Архив: {archive_path}.zip")
        print(f"   📁 Папка: {windows_dir}")
    
    def create_windows_scripts(self, target_dir):
        """Создание скриптов для Windows"""
        
        # 1. Скрипт запуска GUI (основной)
        gui_script = target_dir / "run_gui.bat"
        with open(gui_script, 'w', encoding='utf-8') as f:
            f.write("""@echo off
echo ========================================
echo Учебная Виртуальная Машина (УВМ) - GUI
echo Версия 1.0 (Windows)
echo ========================================
echo.
echo Запуск графического интерфейса...
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    echo Установите Python 3.8 или выше
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

python uvm_gui.py

if errorlevel 1 (
    echo.
    echo Возможные решения:
    echo 1. Установите зависимости: pip install -r requirements.txt
    echo 2. Проверьте путь к Python
    echo 3. Запустите от имени администратора
    pause
)
""")
        
        # 2. Скрипт командной строки
        cli_script = target_dir / "run_cli.bat"
        with open(cli_script, 'w', encoding='utf-8') as f:
            f.write("""@echo off
echo ========================================
echo УВМ - Командная строка
echo ========================================
echo.
echo Доступные команды:
echo.
echo 1. Тесты из спецификации
echo    python uvm_asm.py -t
echo.
echo 2. Ассемблировать программу
echo    python uvm_asm.py -i examples/basic_example.uvm -o program.bin
echo.
echo 3. Выполнить программу
echo    python uvm_interp.py -i program.bin -o dump.xml -r 0-100
echo.
echo 4. Запустить все тесты
echo    python test_stage5.py
echo.
pause
""")
        
        # 3. Скрипт установки
        install_script = target_dir / "install.bat"
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write("""@echo off
echo Установка зависимостей УВМ...
echo.

REM Проверяем pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: pip не найден!
    echo Установите pip: https://pip.pypa.io/en/stable/installation/
    pause
    exit /b 1
)

REM Устанавливаем зависимости если есть requirements.txt
if exist "requirements.txt" (
    echo Установка из requirements.txt...
    python -m pip install -r requirements.txt
) else (
    echo requirements.txt не найден, устанавливаем tkinter...
    python -m pip install tk
)

echo.
echo ✅ Зависимости установлены!
echo.
echo Запустите run_gui.bat для старта
pause
""")
        
        # 4. Скрипт быстрого теста
        test_script = target_dir / "quick_test.bat"
        with open(test_script, 'w', encoding='utf-8') as f:
            f.write("""@echo off
echo Быстрый тест УВМ...
echo.

echo 1. Тестируем ассемблер...
python uvm_asm.py -t

echo.
echo 2. Создаем тестовую программу...
(
echo {"op": "load_const", "address": 100, "constant": 123}
echo {"op": "read", "dst_addr": 200, "src_addr": 100}
) > test.uvm

echo 3. Ассемблируем...
python uvm_asm.py -i test.uvm -o test.bin

echo 4. Выполняем...
python uvm_interp.py -i test.bin -o test_dump.xml -r 90-110

echo.
echo ✅ Тест завершен!
echo Результаты в test_dump.xml
del test.uvm test.bin 2>nul
pause
""")
        
        print("  Созданы скрипты для Windows:")
        print("    • run_gui.bat    - Запуск GUI")
        print("    • run_cli.bat    - Командная строка")
        print("    • install.bat    - Установка зависимостей")
        print("    • quick_test.bat - Быстрый тест")
    
    def build_linux(self):
        """Сборка для Linux"""
        print("\n🐧 Сборка для Linux...")
        
        linux_dir = self.dist_dir / "linux"
        linux_dir.mkdir(exist_ok=True)
        
        # Копируем основные файлы
        for file_name in self.core_files:
            src = self.build_dir / file_name
            if src.exists():
                dst = linux_dir / file_name
                shutil.copy2(src, dst)
        
        # Копируем примеры
        if (self.build_dir / "examples").exists():
            linux_examples = linux_dir / "examples"
            shutil.copytree(self.build_dir / "examples", linux_examples, dirs_exist_ok=True)
        
        # Создаем shell-скрипты
        self.create_linux_scripts(linux_dir)
        
        # Устанавливаем права выполнения
        for script in linux_dir.glob("*.sh"):
            script.chmod(0o755)
        
        # Создаем архив tar.gz
        archive_path = self.dist_dir / "uvm_linux"
        self.create_tar_archive(linux_dir, archive_path)
        
        print(f"✅ Сборка для Linux завершена")
        print(f"   📦 Архив: {archive_path}.tar.gz")
        print(f"   📁 Папка: {linux_dir}")
    
    def create_linux_scripts(self, target_dir):
        """Создание скриптов для Linux"""
        
        # 1. Скрипт запуска GUI
        gui_script = target_dir / "run_gui.sh"
        with open(gui_script, 'w', encoding='utf-8') as f:
            f.write("""#!/bin/bash
echo "========================================"
echo "Учебная Виртуальная Машина (УВМ) - GUI"
echo "Версия 1.0 (Linux)"
echo "========================================"
echo ""
echo "Запуск графического интерфейса..."
echo ""

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python3 не найден!"
    echo "Установите Python3:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-tk"
    echo "  Fedora: sudo dnf install python3 python3-tkinter"
    exit 1
fi

# Запускаем GUI
python3 uvm_gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Возможные решения:"
    echo "1. Установите зависимости: pip3 install -r requirements.txt"
    echo "2. Установите tkinter: sudo apt-get install python3-tk"
    echo "3. Запустите с python3 вместо python"
fi
""")
        
        # 2. Скрипт командной строки
        cli_script = target_dir / "run_cli.sh"
        with open(cli_script, 'w', encoding='utf-8') as f:
            f.write("""#!/bin/bash
echo "========================================"
echo "УВМ - Командная строка"
echo "========================================"
echo ""
echo "Доступные команды:"
echo ""
echo "1. Тесты из спецификации"
echo "   python3 uvm_asm.py -t"
echo ""
echo "2. Ассемблировать программу"
echo "   python3 uvm_asm.py -i examples/basic_example.uvm -o program.bin"
echo ""
echo "3. Выполнить программу"
echo "   python3 uvm_interp.py -i program.bin -o dump.xml -r 0-100"
echo ""
echo "4. Запустить все тесты"
echo "   python3 test_stage5.py"
echo ""
read -p "Нажмите Enter для продолжения..."
""")
        
        # 3. Скрипт установки
        install_script = target_dir / "install.sh"
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write("""#!/bin/bash
echo "Установка зависимостей УВМ..."
echo ""

# Проверяем pip3
if ! command -v pip3 &> /dev/null; then
    echo "Установка pip3..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install python3-pip
    else
        echo "Не удалось установить pip3. Установите вручную."
        exit 1
    fi
fi

# Устанавливаем зависимости если есть requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Установка из requirements.txt..."
    pip3 install -r requirements.txt
else
    echo "requirements.txt не найден, устанавливаем tkinter..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install python3-tk
    elif command -v dnf &> /dev/null; then
        sudo dnf install python3-tkinter
    fi
fi

echo ""
echo "✅ Зависимости установлены!"
echo ""
echo "Запустите ./run_gui.sh для старта"
""")
        
        # 4. README для Linux
        readme_script = target_dir / "README_LINUX.txt"
        with open(readme_script, 'w', encoding='utf-8') as f:
            f.write("""ИНСТРУКЦИЯ ДЛЯ LINUX

1. Дайте права на выполнение:
   chmod +x *.sh

2. Установите зависимости:
   ./install.sh

3. Запустите GUI:
   ./run_gui.sh

Или используйте командную строку:

Ассемблирование:
   python3 uvm_asm.py -i examples/spec_tests.uvm -o program.bin

Выполнение:
   python3 uvm_interp.py -i program.bin -o dump.xml -r 0-100

Требования:
- Python 3.8+
- tkinter (для GUI)
- pip3 (для установки зависимостей)

Установка tkinter:
  Ubuntu/Debian: sudo apt-get install python3-tk
  Fedora:        sudo dnf install python3-tkinter
  Arch:          sudo pacman -S tk
""")
        
        print("  Созданы скрипты для Linux:")
        print("    • run_gui.sh     - Запуск GUI")
        print("    • run_cli.sh     - Командная строка")
        print("    • install.sh     - Установка зависимостей")
        print("    • README_LINUX.txt - Инструкция")
    
    def build_web(self):
        """Сборка веб-версии (статический HTML)"""
        print("\n🌐 Сборка веб-версии...")
        
        web_dir = self.dist_dir / "web"
        web_dir.mkdir(exist_ok=True)
        
        # Создаем веб-страницу
        self.create_web_page(web_dir)
        
        # Копируем примеры
        web_examples = web_dir / "examples"
        web_examples.mkdir(exist_ok=True)
        
        if (self.build_dir / "examples").exists():
            for example in (self.build_dir / "examples").iterdir():
                if example.is_file():
                    shutil.copy2(example, web_examples / example.name)
        
        print("✅ Веб-версия собрана")
        print(f"   📁 Папка: {web_dir}")
        print(f"   🌐 Откройте index.html в браузере")
    
    def create_web_page(self, target_dir):
        """Создание веб-страницы"""
        html_content = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>УВМ - Веб интерфейс</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #1a237e 0%, #311b92 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00bcd4, #2196f3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            color: #bbdefb;
            font-size: 1.2em;
        }
        
        .platforms {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }
        
        .platform-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            transition: transform 0.3s, background 0.3s;
        }
        
        .platform-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.2);
        }
        
        .platform-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        .platform-title {
            font-size: 1.5em;
            margin-bottom: 10px;
            color: #80deea;
        }
        
        .download-btn {
            display: inline-block;
            background: linear-gradient(90deg, #00bcd4, #2196f3);
            color: white;
            padding: 12px 25px;
            border-radius: 25px;
            text-decoration: none;
            margin-top: 15px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(33, 150, 243, 0.4);
        }
        
        .code-example {
            background: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
        }
        
        pre {
            color: #d4d4d4;
            line-height: 1.5;
        }
        
        .instructions {
            margin-top: 40px;
            background: rgba(255, 255, 255, 0.1);
            padding: 25px;
            border-radius: 15px;
        }
        
        .instructions h3 {
            color: #80deea;
            margin-bottom: 15px;
        }
        
        .instructions ol {
            margin-left: 20px;
            line-height: 1.8;
        }
        
        footer {
            margin-top: 40px;
            text-align: center;
            color: #bbdefb;
            font-size: 0.9em;
        }
        
        .highlight {
            background: rgba(0, 188, 212, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            color: #80deea;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Учебная Виртуальная Машина (УВМ)</h1>
            <p class="subtitle">Вариант №24 | Кроссплатформенная реализация</p>
        </header>
        
        <section class="instructions">
            <h3>📋 Описание проекта</h3>
            <p>Учебная Виртуальная Машина (УВМ) - это система для изучения архитектуры ЭВМ, включающая:</p>
            <ul style="margin-left: 20px; margin-top: 10px;">
                <li>Ассемблер для трансляции программ в машинный код</li>
                <li>Интерпретатор для выполнения программ</li>
                <li>Графический интерфейс для удобной работы</li>
                <li>Поддержку команд: load_const, read, write, max</li>
            </ul>
        </section>
        
        <section class="platforms">
            <div class="platform-card">
                <div class="platform-icon">🪟</div>
                <h3 class="platform-title">Windows</h3>
                <p>Запускайте <span class="highlight">run_gui.bat</span> для графического интерфейса или используйте командную строку.</p>
                <p>Требуется Python 3.8+</p>
                <a href="#" class="download-btn" onclick="alert('Скачайте архив из папки dist/windows')">Скачать для Windows</a>
            </div>
            
            <div class="platform-card">
                <div class="platform-icon">🐧</div>
                <h3 class="platform-title">Linux</h3>
                <p>Дайте права <span class="highlight">chmod +x *.sh</span> и запустите <span class="highlight">./run_gui.sh</span></p>
                <p>Требуется Python3 и tkinter</p>
                <a href="#" class="download-btn" onclick="alert('Скачайте архив из папки dist/linux')">Скачать для Linux</a>
            </div>
            
            <div class="platform-card">
                <div class="platform-icon">⚙️</div>
                <h3 class="platform-title">Командная строка</h3>
                <p>Основные команды:</p>
                <pre style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px; margin-top: 10px;">
python uvm_asm.py -t
python uvm_asm.py -i program.uvm -o program.bin
python uvm_interp.py -i program.bin -o dump.xml -r 0-100</pre>
            </div>
        </section>
        
        <section class="code-example">
            <h3>📝 Пример программы УВМ</h3>
            <pre># Тестовая программа
{"op": "load_const", "address": 100, "constant": 42}
{"op": "read", "dst_addr": 200, "src_addr": 100}
{"op": "write", "src_addr": 200, "offset": 5, "base_addr": 300}
{"op": "max", "addr_b": 100, "addr_c": 400, "addr_d": 200}</pre>
        </section>
        
        <section class="instructions">
            <h3>🚀 Быстрый старт</h3>
            <ol>
                <li>Скачайте версию для вашей ОС</li>
                <li>Установите Python 3.8 или выше</li>
                <li>Запустите установочный скрипт (install.bat / install.sh)</li>
                <li>Запустите графический интерфейс</li>
                <li>Используйте примеры из папки examples/</li>
            </ol>
        </section>
        
        <footer>
            <p>Учебный проект по архитектуре ЭВМ | Вариант №24 | ИКБО-09-22</p>
            <p>© 2024 Учебная Виртуальная Машина</p>
        </footer>
    </div>
</body>
</html>"""
        
        with open(target_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def create_zip_archive(self, source_dir, output_path):
        """Создание ZIP архива"""
        print(f"  📦 Создание ZIP архива...")
        
        # Удаляем старый архив если есть
        zip_file = Path(f"{output_path}.zip")
        if zip_file.exists():
            zip_file.unlink()
        
        # Создаем новый архив
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
        
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"  ✅ Архив создан: {zip_file.name} ({size_mb:.2f} MB)")
    
    def create_tar_archive(self, source_dir, output_path):
        """Создание tar.gz архива"""
        print(f"  📦 Создание tar.gz архива...")
        
        # Удаляем старый архив если есть
        tar_file = Path(f"{output_path}.tar.gz")
        if tar_file.exists():
            tar_file.unlink()
        
        # Создаем новый архив
        with tarfile.open(tar_file, "w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)
        
        size_mb = tar_file.stat().st_size / (1024 * 1024)
        print(f"  ✅ Архив создан: {tar_file.name} ({size_mb:.2f} MB)")
    
    def build_all(self):
        """Полная сборка для всех платформ"""
        print("🔨 Начало полной сборки УВМ")
        print("=" * 60)
        
        self.clean()
        self.copy_project_files()
        self.copy_examples()
        
        self.build_windows()
        self.build_linux()
        self.build_web()
        
        print("\n" + "=" * 60)
        print("🎉 Сборка завершена успешно!")
        print("\n📁 Результаты в папке dist/:")
        print("  ├── windows/  - Версия для Windows (ZIP архив)")
        print("  ├── linux/    - Версия для Linux (tar.gz архив)")
        print("  └── web/      - Веб-интерфейс (HTML)")
        print("\n🚀 Для запуска:")
        print("  Windows:  dist\\windows\\run_gui.bat")
        print("  Linux:    dist/linux/run_gui.sh")
        print("  Веб:      dist/web/index.html (открыть в браузере)")
        
        # Показываем размеры
        print("\n📊 Размеры сборок:")
        for platform_dir in self.dist_dir.iterdir():
            if platform_dir.is_dir():
                size_kb = sum(f.stat().st_size for f in platform_dir.rglob('*') if f.is_file()) / 1024
                print(f"  {platform_dir.name:10} - {size_kb:.1f} KB")
    
    def build_specific(self, platform_name):
        """Сборка для конкретной платформы"""
        print(f"🔨 Сборка для {platform_name}")
        print("=" * 60)
        
        self.clean()
        self.copy_project_files()
        self.copy_examples()
        
        if platform_name.lower() == "windows":
            self.build_windows()
        elif platform_name.lower() == "linux":
            self.build_linux()
        elif platform_name.lower() == "web":
            self.build_web()
        else:
            print(f"❌ Неизвестная платформа: {platform_name}")
            print("Доступные: windows, linux, web")
            return
        
        print(f"\n✅ Сборка для {platform_name} завершена")

def main():
    """Основная функция"""
    print("🏗️  Сборщик Учебной Виртуальной Машины (УВМ)")
    print("=" * 60)
    
    builder = UVMBuilder()
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        platform_arg = sys.argv[1].lower()
        if platform_arg in ["windows", "linux", "web"]:
            builder.build_specific(platform_arg)
        elif platform_arg in ["--help", "-h", "help"]:
            print("Использование:")
            print("  python build.py              # Полная сборка")
            print("  python build.py windows      # Только Windows")
            print("  python build.py linux        # Только Linux")
            print("  python build.py web          # Только веб-версия")
            print("  python build.py --help       # Эта справка")
        else:
            print(f"❌ Неизвестный аргумент: {platform_arg}")
            print("Используйте: windows, linux, web или --help")
    else:
        # Полная сборка
        builder.build_all()

if __name__ == "__main__":
    main()
