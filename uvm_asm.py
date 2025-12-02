import argparse
import json

def mask(bits):
    """Создание маски для указанного количества бит"""
    return (1 << bits) - 1

def create_command(op_code, fields):
    """Создание 7-байтовой команды"""
    command = 0
    
    # Код операции (биты 0-4)
    command |= (op_code & mask(5))
    
    if op_code == 19:  # Загрузка константы
        address = fields.get('address', 0)
        constant = fields.get('constant', 0)
        command |= (address & mask(16)) << 5
        command |= (constant & mask(20)) << 21
        
    elif op_code == 3:  # Чтение из памяти
        dst_addr = fields.get('dst_addr', 0)
        src_addr = fields.get('src_addr', 0)
        command |= (dst_addr & mask(16)) << 5
        command |= (src_addr & mask(16)) << 21
        
    elif op_code == 20:  # Запись в память
        src_addr = fields.get('src_addr', 0)
        offset = fields.get('offset', 0)
        base_addr = fields.get('base_addr', 0)
        command |= (src_addr & mask(16)) << 5
        command |= (offset & mask(5)) << 21
        command |= (base_addr & mask(16)) << 26
        
    elif op_code == 7:  # Операция max
        addr_b = fields.get('addr_b', 0)
        addr_c = fields.get('addr_c', 0)
        addr_d = fields.get('addr_d', 0)
        command |= (addr_b & mask(16)) << 5
        command |= (addr_c & mask(16)) << 21
        command |= (addr_d & mask(16)) << 37
        
    return command.to_bytes(7, 'little')

def parse_assembly_language(text):
    """Парсинг языка ассемблера"""
    IR = []
    
    for line_num, line in enumerate(text.strip().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        try:
            cmd_dict = json.loads(line)
            op = cmd_dict.get('op')
            
            if op == 'load_const':
                IR.append(('load_const', cmd_dict['address'], cmd_dict['constant']))
            elif op == 'read':
                IR.append(('read', cmd_dict['dst_addr'], cmd_dict['src_addr']))
            elif op == 'write':
                IR.append(('write', cmd_dict['src_addr'], cmd_dict['offset'], cmd_dict['base_addr']))
            elif op == 'max':
                IR.append(('max', cmd_dict['addr_b'], cmd_dict['addr_c'], cmd_dict['addr_d']))
            else:
                print(f"Неизвестная операция: '{op}'")
                
        except json.JSONDecodeError:
            print(f"Ошибка JSON в строке {line_num}")
        except KeyError as e:
            print(f"Ошибка: отсутствует поле {e}")
    
    return IR

def assemble_ir(IR):
    """Преобразование IR в машинный код"""
    bytecode = bytes()
    
    for cmd in IR:
        op = cmd[0]
        
        if op == 'load_const':
            bytecode += create_command(19, {'address': cmd[1], 'constant': cmd[2]})
        elif op == 'read':
            bytecode += create_command(3, {'dst_addr': cmd[1], 'src_addr': cmd[2]})
        elif op == 'write':
            bytecode += create_command(20, {'src_addr': cmd[1], 'offset': cmd[2], 'base_addr': cmd[3]})
        elif op == 'max':
            bytecode += create_command(7, {'addr_b': cmd[1], 'addr_c': cmd[2], 'addr_d': cmd[3]})
    
    return bytecode

def format_bytecode_exactly_like_spec(bytecode):
    """Форматирование байткода ТОЧНО как в спецификации"""
    formatted_bytes = []
    
    for i in range(0, len(bytecode), 7):
        chunk = bytecode[i:i+7]
        # Форматируем каждый байт как 0xXX
        hex_bytes = [f"0x{b:02X}" for b in chunk]
        # Объединяем через запятую и пробел
        formatted_line = ", ".join(hex_bytes)
        formatted_bytes.append(formatted_line)
    
    return formatted_bytes

def display_test_results():
    """Вывод тестовых результатов ТОЧНО как в спецификации"""
    print("\n" + "="*60)
    print("ТЕСТОВЫЕ ПРИМЕРЫ ИЗ СПЕЦИФИКАЦИИ УВМ:")
    print("="*60)
    
    tests = [
        ("Загрузка константы (A=19, B=825, C=559)", 
         19, {'address': 825, 'constant': 559},
         "0x33, 0x67, 0xE0, 0x45, 0x00, 0x00, 0x00"),
        
        ("Чтение из памяти (A=3, B=84, C=215)", 
         3, {'dst_addr': 84, 'src_addr': 215},
         "0x83, 0x0A, 0xE0, 0x1A, 0x00, 0x00, 0x00"),
        
        ("Запись в память (A=20, B=193, C=30, D=352)", 
         20, {'src_addr': 193, 'offset': 30, 'base_addr': 352},
         "0x34, 0x18, 0xC0, 0x83, 0x05, 0x00, 0x00"),
        
        ("Бинарная операция max (A=7, B=782, C=367, D=565)", 
         7, {'addr_b': 782, 'addr_c': 367, 'addr_d': 565},
         "0x07, 0x61, 0x80, 0x0D, 0xA0, 0xB6, 0xA0")
    ]
    
    for name, op_code, fields, expected in tests:
        print(f"\n{name}:")
        cmd_bytes = create_command(op_code, fields)
        
        # Форматируем ТОЧНО как в спецификации
        hex_bytes = [f"0x{b:02X}" for b in cmd_bytes]
        formatted = ", ".join(hex_bytes)
        
        print(f"Ответ: {formatted}")
        
        # Проверка
        if formatted == expected:
            print(f"  ✓ Корректно")
        else:
            print(f"  ✗ Ошибка!")
            print(f"    Ожидалось: {expected}")
            print(f"    Получено:  {formatted}")
    
    print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description='Ассемблер Учебной Виртуальной Машины (УВМ)')
    parser.add_argument('-i', '--input', required=False, help='Путь к исходному файлу')
    parser.add_argument('-o', '--output', required=False, help='Путь к двоичному файлу-результату')
    parser.add_argument('-t', '--test', action='store_true', help='Показать тестовые примеры')
    parser.add_argument('-v', '--verbose', action='store_true', help='Подробный вывод')
    parser.add_argument('--format', action='store_true', help='Вывод в формате спецификации')
    
    args = parser.parse_args()
    
    # Если указан флаг -t, показываем тесты
    if args.test:
        display_test_results()
        return
    
    # Если указаны input и output, выполняем ассемблирование
    if args.input and args.output:
        with open(args.input, 'r', encoding='utf-8') as file:
            text = file.read()
        
        IR = parse_assembly_language(text)
        bytecode = assemble_ir(IR)
        
        with open(args.output, 'wb') as output_file:
            output_file.write(bytecode)
        
        print(f"\n✅ Ассемблирование завершено!")
        print(f"📊 Статистика:")
        print(f"   Количество команд: {len(IR)}")
        print(f"   Размер бинарного файла: {len(bytecode)} байт")
        
        # Вывод в формате спецификации (если указан флаг или verbose)
        if args.format or args.verbose:
            print(f"\n🎯 Результат ассемблирования в формате спецификации:")
            print("="*70)
            
            formatted_lines = format_bytecode_exactly_like_spec(bytecode)
            
            for i, line in enumerate(formatted_lines):
                print(f"Команда {i}: {line}")
            
            print("="*70)
            
        # Если не verbose, показываем только одну команду для примера
        elif len(IR) > 0:
            print(f"\n📝 Пример вывода (первая команда):")
            first_chunk = bytecode[0:7]
            hex_bytes = [f"0x{b:02X}" for b in first_chunk]
            formatted = ", ".join(hex_bytes)
            print(f"  {formatted}")
            print(f"  (используйте -v для полного вывода)")
            
    else:
        print("Использование:")
        print("  python uvm_asm.py -t                         # Показать тестовые примеры")
        print("  python uvm_asm.py -i input.uvm -o output.bin # Ассемблировать программу")
        print("  python uvm_asm.py -i input.uvm -o output.bin -v --format # Подробный вывод в формате спецификации")

if __name__ == "__main__":
    main()