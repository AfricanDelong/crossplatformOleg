#!/usr/bin/env python3
"""
Кроссплатформенное GUI приложение Учебной Виртуальной Машины (УВМ)
Поддерживает: Windows, Linux, macOS
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import os
import sys
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# Импортируем функции из наших модулей
try:
    from uvm_asm import parse_assembly_language, assemble_ir, display_test_results
    from uvm_interp import execute_program, save_xml_dump
    HAS_MODULES = True
except ImportError:
    HAS_MODULES = False
    print("⚠  Модули uvm_asm и uvm_interp не найдены. Используется fallback-режим.")

class UVM_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Учебная Виртуальная Машина (УВМ) v1.0")
        self.root.geometry("1200x800")
        
        # Переменные
        self.current_file = None
        self.program_text = ""
        self.memory_dump = ""
        self.assembly_result = ""
        
        # Создаем интерфейс
        self.setup_ui()
        
        # Загружаем пример программы
        self.load_example_program()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Создаем меню
        self.create_menu()
        
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов строк и столбцов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Панель инструментов
        toolbar = ttk.Frame(main_frame)
        toolbar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Кнопки на панели инструментов
        ttk.Button(toolbar, text="📁 Открыть", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Сохранить", command=self.save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Сохранить как...", command=self.save_as_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="▶ Ассемблировать", command=self.assemble_program, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⚡ Выполнить", command=self.execute_program,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🧪 Тесты", command=self.run_tests).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="❓ Справка", command=self.show_help).pack(side=tk.LEFT, padx=2)
        
        # Стиль для акцентных кнопок
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="white", background="#0078D7")
        
        # Левая панель: редактор программы
        left_frame = ttk.LabelFrame(main_frame, text="Редактор программы (формат JSON)", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        self.program_editor = scrolledtext.ScrolledText(left_frame, width=50, height=30,
                                                       font=("Courier New", 10))
        self.program_editor.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Правая панель: вывод результатов
        right_frame = ttk.LabelFrame(main_frame, text="Результаты и дамп памяти", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # Notebook для вкладок
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Вкладка 1: Результаты ассемблирования
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="Ассемблирование")
        tab1.columnconfigure(0, weight=1)
        tab1.rowconfigure(0, weight=1)
        
        self.asm_output = scrolledtext.ScrolledText(tab1, width=50, height=15,
                                                   font=("Courier New", 9))
        self.asm_output.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.asm_output.config(state=tk.DISABLED)
        
        # Вкладка 2: Дамп памяти
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="Дамп памяти")
        tab2.columnconfigure(0, weight=1)
        tab2.rowconfigure(0, weight=1)
        
        self.memory_output = scrolledtext.ScrolledText(tab2, width=50, height=15,
                                                      font=("Courier New", 9))
        self.memory_output.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.memory_output.config(state=tk.DISABLED)
        
        # Вкладка 3: Консоль
        tab3 = ttk.Frame(self.notebook)
        self.notebook.add(tab3, text="Консоль")
        tab3.columnconfigure(0, weight=1)
        tab3.rowconfigure(0, weight=1)
        
        self.console_output = scrolledtext.ScrolledText(tab3, width=50, height=15,
                                                       font=("Consolas", 9))
        self.console_output.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.console_output.config(state=tk.DISABLED)
        
        # Статус бар
        self.status_bar = ttk.Label(main_frame, text="Готово", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def create_menu(self):
        """Создание меню приложения"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit, accelerator="Alt+F4")
        
        # Меню Правка
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Вырезать", command=self.cut_text)
        edit_menu.add_command(label="Копировать", command=self.copy_text)
        edit_menu.add_command(label="Вставить", command=self.paste_text)
        
        # Меню Выполнение
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Выполнение", menu=run_menu)
        run_menu.add_command(label="Ассемблировать", command=self.assemble_program, accelerator="F5")
        run_menu.add_command(label="Выполнить программу", command=self.execute_program, accelerator="F6")
        run_menu.add_separator()
        run_menu.add_command(label="Запустить тесты", command=self.run_tests)
        
        # Меню Примеры
        examples_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Примеры", menu=examples_menu)
        examples_menu.add_command(label="Базовый пример", command=self.load_basic_example)
        examples_menu.add_command(label="Тест векторов (Этап 5)", command=self.load_vector_example)
        examples_menu.add_command(label="Тест матрицы", command=self.load_matrix_example)
        examples_menu.add_command(label="Тест временных рядов", command=self.load_timeseries_example)
        
        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        help_menu.add_command(label="Справка по языку", command=self.show_language_help)
        help_menu.add_command(label="Тестовые примеры", command=self.show_test_examples)
        
        # Привязка клавиш
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<F5>', lambda e: self.assemble_program())
        self.root.bind('<F6>', lambda e: self.execute_program())
        
    def update_status(self, message):
        """Обновление статусной строки"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
        
    def log_to_console(self, message):
        """Вывод сообщения в консоль"""
        self.console_output.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_output.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console_output.see(tk.END)
        self.console_output.config(state=tk.DISABLED)
        
    def load_example_program(self):
        """Загрузка примера программы"""
        example = '''# Пример программы для УВМ
# Загрузка константы: A=19, B=825, C=559
{"op": "load_const", "address": 825, "constant": 559}

# Чтение из памяти: A=3, B=84, C=215
{"op": "read", "dst_addr": 84, "src_addr": 215}

# Запись в память: A=20, B=193, C=30, D=352
{"op": "write", "src_addr": 193, "offset": 30, "base_addr": 352}

# Операция max: A=7, B=782, C=367, D=565
{"op": "max", "addr_b": 782, "addr_c": 367, "addr_d": 565}'''
        
        self.program_editor.delete(1.0, tk.END)
        self.program_editor.insert(1.0, example)
        
    def load_basic_example(self):
        """Загрузка базового примера"""
        example = '''# Базовые операции УВМ
{"op": "load_const", "address": 100, "constant": 42}
{"op": "load_const", "address": 101, "constant": 100}
{"op": "read", "dst_addr": 102, "src_addr": 100}
{"op": "write", "src_addr": 101, "offset": 5, "base_addr": 200}
{"op": "max", "addr_b": 100, "addr_c": 103, "addr_d": 101}'''
        
        self.program_editor.delete(1.0, tk.END)
        self.program_editor.insert(1.0, example)
        self.log_to_console("Загружен базовый пример")
        
    def load_vector_example(self):
        """Загрузка примера с векторами (Этап 5)"""
        example = '''# Пример: MAX над двумя векторами длины 3
{"op": "load_const", "address": 1000, "constant": 17}
{"op": "load_const", "address": 1001, "constant": 42}
{"op": "load_const", "address": 1002, "constant": 8}

{"op": "load_const", "address": 1010, "constant": 23}
{"op": "load_const", "address": 1011, "constant": 15}
{"op": "load_const", "address": 1012, "constant": 67}

{"op": "max", "addr_b": 1000, "addr_c": 1020, "addr_d": 1010}
{"op": "max", "addr_b": 1001, "addr_c": 1021, "addr_d": 1011}
{"op": "max", "addr_b": 1002, "addr_c": 1022, "addr_d": 1012}'''
        
        self.program_editor.delete(1.0, tk.END)
        self.program_editor.insert(1.0, example)
        self.log_to_console("Загружен пример с векторами")
        
    def load_matrix_example(self):
        """Загрузка примера с матрицей"""
        example = '''# Пример: матрица 2x2
{"op": "load_const", "address": 2000, "constant": 5}
{"op": "load_const", "address": 2001, "constant": 8}
{"op": "load_const", "address": 2002, "constant": 3}
{"op": "load_const", "address": 2003, "constant": 6}

{"op": "max", "addr_b": 2000, "addr_c": 2010, "addr_d": 2001}
{"op": "max", "addr_b": 2010, "addr_c": 2011, "addr_d": 2002}
{"op": "max", "addr_b": 2011, "addr_c": 2012, "addr_d": 2003}'''
        
        self.program_editor.delete(1.0, tk.END)
        self.program_editor.insert(1.0, example)
        self.log_to_console("Загружен пример с матрицей")
        
    def load_timeseries_example(self):
        """Загрузка примера с временными рядами"""
        example = '''# Пример: временные ряды
{"op": "load_const", "address": 3000, "constant": 45}
{"op": "load_const", "address": 3001, "constant": 52}
{"op": "load_const", "address": 3002, "constant": 48}

{"op": "load_const", "address": 3010, "constant": 43}
{"op": "load_const", "address": 3011, "constant": 56}
{"op": "load_const", "address": 3012, "constant": 49}

{"op": "max", "addr_b": 3000, "addr_c": 3020, "addr_d": 3010}
{"op": "max", "addr_b": 3001, "addr_c": 3021, "addr_d": 3011}
{"op": "max", "addr_b": 3002, "addr_c": 3022, "addr_d": 3012}'''
        
        self.program_editor.delete(1.0, tk.END)
        self.program_editor.insert(1.0, example)
        self.log_to_console("Загружен пример с временными рядами")
        
    def new_file(self):
        """Создание нового файла"""
        self.program_editor.delete(1.0, tk.END)
        self.current_file = None
        self.update_status("Новый файл")
        self.log_to_console("Создан новый файл")
        
    def open_file(self):
        """Открытие файла"""
        filetypes = [
            ("Файлы УВМ", "*.uvm"),
            ("Текстовые файлы", "*.txt"),
            ("Все файлы", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Открыть файл программы",
            filetypes=filetypes
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.program_editor.delete(1.0, tk.END)
                self.program_editor.insert(1.0, content)
                self.current_file = filename
                self.update_status(f"Открыт файл: {os.path.basename(filename)}")
                self.log_to_console(f"Открыт файл: {filename}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{str(e)}")
                
    def save_file(self):
        """Сохранение файла"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
            
    def save_as_file(self):
        """Сохранение файла как..."""
        filetypes = [
            ("Файлы УВМ", "*.uvm"),
            ("Текстовые файлы", "*.txt"),
            ("Все файлы", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="Сохранить файл",
            defaultextension=".uvm",
            filetypes=filetypes
        )
        
        if filename:
            self.save_to_file(filename)
            self.current_file = filename
            
    def save_to_file(self, filename):
        """Сохранение в файл"""
        try:
            content = self.program_editor.get(1.0, tk.END)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.update_status(f"Сохранен файл: {os.path.basename(filename)}")
            self.log_to_console(f"Сохранен файл: {filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
            
    def cut_text(self):
        """Вырезать текст"""
        self.program_editor.event_generate("<<Cut>>")
        
    def copy_text(self):
        """Копировать текст"""
        self.program_editor.event_generate("<<Copy>>")
        
    def paste_text(self):
        """Вставить текст"""
        self.program_editor.event_generate("<<Paste>>")
        
    def format_bytecode_spec_like(self, bytecode):
        """Форматирование байткода ТОЧНО как в спецификации: 0x33, 0x67, 0xE0, ..."""
        output_lines = []
        
        # Группируем байты по 7 (размер команды)
        for i in range(0, len(bytecode), 7):
            chunk = bytecode[i:i+7]
            # Форматируем каждый байт как 0xXX
            hex_bytes = [f"0x{b:02X}" for b in chunk]
            # Объединяем через запятую и пробел
            formatted_line = ", ".join(hex_bytes)
            output_lines.append(f"Команда {i//7}: {formatted_line}")
        
        return "\n".join(output_lines)
        
    def assemble_program(self):
        """Ассемблирование программы"""
        program_text = self.program_editor.get(1.0, tk.END)
        
        if not program_text.strip():
            messagebox.showwarning("Предупреждение", "Программа пуста!")
            return
            
        self.update_status("Ассемблирование...")
        self.log_to_console("Начало ассемблирования")
        
        try:
            if HAS_MODULES:
                # Используем наши модули
                IR = parse_assembly_language(program_text)
                bytecode = assemble_ir(IR)
                
                # Сохраняем временный файл
                with open('temp_program.bin', 'wb') as f:
                    f.write(bytecode)
                    
                # Выводим результаты ТОЧНО как в спецификации
                self.asm_output.config(state=tk.NORMAL)
                self.asm_output.delete(1.0, tk.END)
                
                output = f"✅ Ассемблирование успешно!\n"
                output += f"Команд: {len(IR)}\n"
                output += f"Размер: {len(bytecode)} байт\n\n"
                output += "🎯 Байткод в формате спецификации:\n"
                output += "=" * 70 + "\n"
                
                # Используем наш новый метод для форматирования
                formatted_output = self.format_bytecode_spec_like(bytecode)
                output += formatted_output
                
                output += "\n" + "=" * 70 + "\n"
                
                self.asm_output.insert(1.0, output)
                self.asm_output.config(state=tk.DISABLED)
                
                self.notebook.select(0)  # Переключаемся на вкладку ассемблирования
                self.update_status(f"Ассемблировано {len(IR)} команд")
                self.log_to_console(f"Ассемблирование успешно: {len(IR)} команд, {len(bytecode)} байт")
                
            else:
                # Fallback: используем внешний скрипт
                with open('temp_program.uvm', 'w', encoding='utf-8') as f:
                    f.write(program_text)
                    
                result = subprocess.run(
                    ['python', 'uvm_asm.py', '-i', 'temp_program.uvm', '-o', 'temp_program.bin', '--format'],
                    capture_output=True,
                    text=True
                )
                
                self.asm_output.config(state=tk.NORMAL)
                self.asm_output.delete(1.0, tk.END)
                
                if result.returncode == 0:
                    self.asm_output.insert(1.0, result.stdout)
                    self.log_to_console("Ассемблирование через внешний скрипт успешно")
                else:
                    self.asm_output.insert(1.0, f"Ошибка:\n{result.stderr}")
                    self.log_to_console(f"Ошибка ассемблирования: {result.stderr}")
                    
                self.asm_output.config(state=tk.DISABLED)
                self.notebook.select(0)
                
        except Exception as e:
            messagebox.showerror("Ошибка ассемблирования", str(e))
            self.log_to_console(f"Ошибка ассемблирования: {str(e)}")
            self.update_status("Ошибка ассемблирования")
            
    def execute_program(self):
        """Выполнение программы"""
        self.update_status("Выполнение программы...")
        self.log_to_console("Начало выполнения программы")
        
        try:
            if HAS_MODULES:
                # Загружаем байткод
                with open('temp_program.bin', 'rb') as f:
                    bytecode = f.read()
                    
                # Выполняем программу
                memory = execute_program(bytecode, data_memory_size=4096, verbose=False)
                
                # Создаем XML дамп
                xml_content = self.create_xml_dump(memory, "0-100")
                
                # Выводим дамп памяти
                self.memory_output.config(state=tk.NORMAL)
                self.memory_output.delete(1.0, tk.END)
                
                # Парсим XML для красивого отображения
                try:
                    root = ET.fromstring(xml_content)
                    output = "Дамп памяти (первые 50 ячеек):\n"
                    output += "=" * 50 + "\n"
                    
                    cells = root.findall('.//cell')
                    for i, cell in enumerate(cells[:50]):
                        addr = cell.get('address')
                        value = cell.get('value')
                        output += f"[{addr:4}] = {value}\n"
                        
                    if len(cells) > 50:
                        output += f"... и еще {len(cells) - 50} ячеек\n"
                        
                except:
                    output = xml_content
                    
                self.memory_output.insert(1.0, output)
                self.memory_output.config(state=tk.DISABLED)
                
                self.notebook.select(1)  # Переключаемся на вкладку дампа памяти
                self.update_status("Программа выполнена успешно")
                self.log_to_console("Программа выполнена успешно")
                
            else:
                # Fallback: используем внешний скрипт
                result = subprocess.run(
                    ['python', 'uvm_interp.py', '-i', 'temp_program.bin', 
                     '-o', 'temp_dump.xml', '-r', '0-100'],
                    capture_output=True,
                    text=True
                )
                
                self.memory_output.config(state=tk.NORMAL)
                self.memory_output.delete(1.0, tk.END)
                
                if result.returncode == 0:
                    # Читаем XML дамп
                    try:
                        with open('temp_dump.xml', 'r', encoding='utf-8') as f:
                            xml_content = f.read()
                            
                        root = ET.fromstring(xml_content)
                        output = "Дамп памяти:\n"
                        output += "=" * 50 + "\n"
                        
                        cells = root.findall('.//cell')
                        for i, cell in enumerate(cells[:50]):
                            addr = cell.get('address')
                            value = cell.get('value')
                            output += f"[{addr:4}] = {value}\n"
                            
                        if len(cells) > 50:
                            output += f"... и еще {len(cells) - 50} ячеек\n"
                            
                    except Exception as e:
                        output = f"Результат выполнения:\n{result.stdout}\n\nXML дамп:\n{xml_content}"
                        
                    self.memory_output.insert(1.0, output)
                    self.log_to_console("Выполнение через внешний скрипт успешно")
                else:
                    self.memory_output.insert(1.0, f"Ошибка:\n{result.stderr}")
                    self.log_to_console(f"Ошибка выполнения: {result.stderr}")
                    
                self.memory_output.config(state=tk.DISABLED)
                self.notebook.select(1)
                
        except FileNotFoundError:
            messagebox.showwarning("Предупреждение", 
                                 "Сначала нужно ассемблировать программу!")
            self.log_to_console("Ошибка: программа не ассемблирована")
        except Exception as e:
            messagebox.showerror("Ошибка выполнения", str(e))
            self.log_to_console(f"Ошибка выполнения: {str(e)}")
            
    def create_xml_dump(self, memory, addr_range):
        """Создание XML дампа памяти"""
        root = ET.Element("memory_dump")
        meta = ET.SubElement(root, "metadata")
        ET.SubElement(meta, "total_cells").text = str(len(memory))
        ET.SubElement(meta, "dump_range").text = addr_range
        ET.SubElement(meta, "timestamp").text = datetime.now().isoformat()
        
        data = ET.SubElement(root, "data")
        
        if '-' in addr_range:
            start, end = map(int, addr_range.split('-'))
        else:
            start = end = int(addr_range)
            
        start = max(0, start)
        end = min(len(memory) - 1, end)
        
        for addr in range(start, end + 1):
            cell = ET.SubElement(data, "cell")
            cell.set("address", str(addr))
            cell.set("value", str(memory[addr]))
            cell.set("hex", f"0x{memory[addr]:X}")
            
        # Преобразуем в строку с форматированием
        from xml.dom import minidom
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        return xml_str
        
    def run_tests(self):
        """Запуск тестов"""
        self.update_status("Запуск тестов...")
        self.log_to_console("Запуск тестовых примеров")
        
        try:
            if HAS_MODULES:
                display_test_results()
                self.log_to_console("Тестовые примеры выполнены")
            else:
                result = subprocess.run(
                    ['python', 'uvm_asm.py', '-t'],
                    capture_output=True,
                    text=True
                )
                
                self.console_output.config(state=tk.NORMAL)
                self.console_output.delete(1.0, tk.END)
                self.console_output.insert(1.0, result.stdout)
                self.console_output.config(state=tk.DISABLED)
                
                self.notebook.select(2)  # Переключаемся на консоль
                self.log_to_console("Тесты выполнены через внешний скрипт")
                
            self.update_status("Тесты выполнены")
            
        except Exception as e:
            messagebox.showerror("Ошибка тестирования", str(e))
            self.log_to_console(f"Ошибка тестирования: {str(e)}")
            
    def show_help(self):
        """Показать справку"""
        help_text = """Учебная Виртуальная Машина (УВМ) - GUI версия

Основные возможности:
1. Редактирование программ на языке ассемблера УВМ
2. Ассемблирование программ (F5)
3. Выполнение программ (F6)
4. Просмотр дампа памяти
5. Запуск тестовых примеров

Язык ассемблера УВМ использует JSON-формат:
- load_const: {"op": "load_const", "address": N, "constant": M}
- read: {"op": "read", "dst_addr": N, "src_addr": M}
- write: {"op": "write", "src_addr": N, "offset": O, "base_addr": B}
- max: {"op": "max", "addr_b": B, "addr_c": C, "addr_d": D}

Примеры программ доступны в меню "Примеры"."""
        
        messagebox.showinfo("Справка", help_text)
        
    def show_about(self):
        """Показать информацию о программе"""
        about_text = """Учебная Виртуальная Машина (УВМ)
Версия: 1.0
Вариант: №24

Разработано для курса "Архитектура ЭВМ"
Кроссплатформенное GUI приложение

Поддерживаемые платформы:
- Windows
- Linux
- macOS

© 2024 УВМ Проект"""
        
        messagebox.showinfo("О программе", about_text)
        
    def show_language_help(self):
        """Показать справку по языку"""
        help_text = """ФОРМАТ КОМАНД УВМ (JSON):

1. ЗАГРУЗКА КОНСТАНТЫ:
   {"op": "load_const", "address": A, "constant": C}
   Пример: {"op": "load_const", "address": 100, "constant": 42}

2. ЧТЕНИЕ ИЗ ПАМЯТИ:
   {"op": "read", "dst_addr": D, "src_addr": S}
   Пример: {"op": "read", "dst_addr": 200, "src_addr": 100}

3. ЗАПИСЬ В ПАМЯТЬ:
   {"op": "write", "src_addr": S, "offset": O, "base_addr": B}
   Пример: {"op": "write", "src_addr": 200, "offset": 5, "base_addr": 300}

4. ОПЕРАЦИЯ MAX:
   {"op": "max", "addr_b": B, "addr_c": C, "addr_d": D}
   Пример: {"op": "max", "addr_b": 100, "addr_c": 200, "addr_d": 150}

ПРИМЕЧАНИЯ:
- Адреса: 0-65535
- Константы: 0-1048575
- Смещения: 0-31"""
        
        messagebox.showinfo("Справка по языку УВМ", help_text)
        
    def show_test_examples(self):
        """Показать тестовые примеры"""
        examples = """ТЕСТОВЫЕ ПРИМЕРЫ ИЗ СПЕЦИФИКАЦИИ:

1. Загрузка константы (A=19, B=825, C=559):
   {"op": "load_const", "address": 825, "constant": 559}

2. Чтение из памяти (A=3, B=84, C=215):
   {"op": "read", "dst_addr": 84, "src_addr": 215}

3. Запись в память (A=20, B=193, C=30, D=352):
   {"op": "write", "src_addr": 193, "offset": 30, "base_addr": 352}

4. Операция max (A=7, B=782, C=367, D=565):
   {"op": "max", "addr_b": 782, "addr_c": 367, "addr_d": 565}

Эти примеры можно запустить через меню "Выполнение" -> "Запустить тесты"."""
        
        messagebox.showinfo("Тестовые примеры", examples)

def main():
    """Запуск GUI приложения"""
    root = tk.Tk()
    
    # Устанавливаем иконку (если есть)
    try:
        root.iconbitmap('uvm_icon.ico')
    except:
        pass
        
    app = UVM_GUI(root)
    
    # Центрируем окно
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()