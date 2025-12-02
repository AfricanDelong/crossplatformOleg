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
      python uvm_asm.py -i input.uvm -o program.bin

3. ФОРМАТ ПРОГРАММ (program.uvm):
   Каждая команда в отдельной строке JSON:
   
   {"op": "load_const", "address": 100, "constant": 42}
   {"op": "read", "dst_addr": 200, "src_addr": 100}
   {"op": "write", "src_addr": 200, "offset": 5, "base_addr": 300}
   {"op": "max", "addr_b": 100, "addr_c": 400, "addr_d": 200}


