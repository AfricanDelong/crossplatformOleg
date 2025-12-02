БЫСТРЫЙ СТАРТ - УЧЕБНАЯ ВИРТУАЛЬНАЯ МАШИНА

1. УСТАНОВКА:
   - Убедитесь, что установлен Python 3.8+
   - Для GUI: установите tkinter (обычно идет с Python)

2. ЗАПУСК (выберите один способ):

   А) ГРАФИЧЕСКИЙ ИНТЕРФЕЙС:
      python uvm_gui.py

   Б) КОМАНДНАЯ СТРОКА:
      # Тесты из спецификации
      python uvm_asm.py -t
      
      # Ассемблировать программу
      python uvm_asm.py -i program.uvm -o program.bin
      
      # Выполнить программу
      python uvm_interp.py -i program.bin -o dump.xml -r 0-100

3. ФОРМАТ ПРОГРАММ (program.uvm):
   Каждая команда в отдельной строке JSON:
   
   {"op": "load_const", "address": 100, "constant": 42}
   {"op": "read", "dst_addr": 200, "src_addr": 100}
   {"op": "write", "src_addr": 200, "offset": 5, "base_addr": 300}
   {"op": "max", "addr_b": 100, "addr_c": 400, "addr_d": 200}

4. ПРИМЕР ПРОГРАММЫ:
   Скопируйте этот код в test.uvm:
   
   # Простая тестовая программа
   {"op": "load_const", "address": 500, "constant": 10}
   {"op": "load_const", "address": 501, "constant": 20}
   {"op": "max", "addr_b": 500, "addr_c": 502, "addr_d": 501}

5. ЗАПУСТИТЕ:
   python uvm_asm.py -i test.uvm -o test.bin -v
   python uvm_interp.py -i test.bin -o dump.xml -r 500-502

6. РЕЗУЛЬТАТ:
   - memory[500] = 10
   - memory[501] = 20
   - memory[502] = 20 (результат max(10, 20))

7. ГОРЯЧИЕ КЛАВИШИ В GUI:
   F5 - Ассемблировать
   F6 - Выполнить
   Ctrl+S - Сохранить
   Ctrl+O - Открыть
   Alt+F4 - Выход

8. СБОРКА ДЛЯ ДРУГИХ ПЛАТФОРМ:
   python build.py        # Все платформы
   python build.py windows  # Только Windows
   python build.py linux    # Только Linux

СМ. README.txt ДЛЯ ПОДРОБНОЙ ИНФОРМАЦИИ
