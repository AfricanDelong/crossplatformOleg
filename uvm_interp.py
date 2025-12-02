import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

def mask(bits):
    """Создание маски для указанного количества бит"""
    return (1 << bits) - 1

def decode_command(command_bytes):
    """Декодирование команды из байтов в промежуточное представление"""
    if len(command_bytes) != 7:
        raise ValueError(f"Некорректная длина команды: {len(command_bytes)} байт")
    
    command = int.from_bytes(command_bytes, 'little')
    op = command & mask(5)
    
    if op == 19:  # Загрузка константы
        address = (command >> 5) & mask(16)
        constant = (command >> 21) & mask(20)
        return ('load_const', address, constant)
        
    elif op == 3:  # Чтение из памяти
        dst_addr = (command >> 5) & mask(16)
        src_addr = (command >> 21) & mask(16)
        return ('read', dst_addr, src_addr)
        
    elif op == 20:  # Запись в память
        src_addr = (command >> 5) & mask(16)
        offset = (command >> 21) & mask(5)
        base_addr = (command >> 26) & mask(16)
        return ('write', src_addr, offset, base_addr)
        
    elif op == 7:  # Бинарная операция max
        addr_b = (command >> 5) & mask(16)
        addr_c = (command >> 21) & mask(16)
        addr_d = (command >> 37) & mask(16)
        return ('max', addr_b, addr_c, addr_d)
        
    else:
        return ('unknown', op)

def execute_program(bytecode, data_memory_size=4096, verbose=False):
    """
    Выполнение программы УВМ с поддержкой АЛУ операций
    """
    # Раздельная память: данные отдельно
    data_memory = [0] * data_memory_size
    
    # Память команд - это сам байткод
    code_memory = bytecode
    
    if verbose:
        print(f"⚙  Настройки исполнения:")
        print(f"   Загружено команд: {len(code_memory) // 7}")
        print(f"   Память данных: {data_memory_size} ячеек")
    
    # Основной цикл интерпретации
    ip = 0  # Instruction Pointer
    command_count = 0
    max_operations = 0
    
    while ip < len(code_memory):
        if ip + 7 > len(code_memory):
            break
            
        # Чтение команды из памяти команд
        command_bytes = code_memory[ip:ip+7]
        
        # Декодирование в промежуточное представление
        decoded_cmd = decode_command(command_bytes)
        
        # Выполнение команды
        op = decoded_cmd[0]
        
        if op == 'load_const':
            _, address, constant = decoded_cmd
            data_memory[address] = constant
            if verbose and command_count < 10:
                print(f"  [{command_count:3}] load_const: memory[{address}] = {constant}")
            
        elif op == 'read':
            _, dst_addr, src_addr = decoded_cmd
            data_memory[dst_addr] = data_memory[src_addr]
            if verbose and command_count < 10:
                print(f"  [{command_count:3}] read: memory[{dst_addr}] = memory[{src_addr}] = {data_memory[dst_addr]}")
            
        elif op == 'write':
            _, src_addr, offset, base_addr = decoded_cmd
            target_addr = base_addr + offset
            data_memory[target_addr] = data_memory[src_addr]
            if verbose and command_count < 10:
                print(f"  [{command_count:3}] write: memory[{target_addr}] = memory[{src_addr}] = {data_memory[target_addr]}")
            
        elif op == 'max':
            _, addr_b, addr_c, addr_d = decoded_cmd
            val_b = data_memory[addr_b]
            val_d = data_memory[addr_d]
            result = max(val_b, val_d)
            data_memory[addr_c] = result
            max_operations += 1
            
            if verbose:
                print(f"  [{command_count:3}] 🔷 MAX операция:")
                print(f"       addr_b[{addr_b}] = {val_b}")
                print(f"       addr_d[{addr_d}] = {val_d}")
                print(f"       max({val_b}, {val_d}) = {result}")
                print(f"       ➡ Результат в memory[{addr_c}] = {result}")
            
        elif op == 'unknown':
            print(f"⚠ Неизвестная операция: {decoded_cmd[1]}")
            
        ip += 7
        command_count += 1
    
    print(f"\n📊 Статистика выполнения:")
    print(f"   Всего команд: {command_count}")
    print(f"   Операций MAX: {max_operations}")
    
    return data_memory

def save_xml_dump(memory, output_file, addr_range):
    """
    Сохранение дампа памяти в формате XML
    """
    try:
        # Поддержка нескольких диапазонов через запятую
        ranges = []
        if ',' in addr_range:
            range_parts = addr_range.split(',')
            for part in range_parts:
                if '-' in part:
                    start, end = map(int, part.strip().split('-'))
                    ranges.append((start, end))
                else:
                    addr = int(part.strip())
                    ranges.append((addr, addr))
        else:
            if '-' in addr_range:
                start, end = map(int, addr_range.split('-'))
                ranges.append((start, end))
            else:
                addr = int(addr_range)
                ranges.append((addr, addr))
        
        # Создание XML структуры
        root = ET.Element("memory_dump")
        
        # Добавление метаинформации
        meta = ET.SubElement(root, "metadata")
        ET.SubElement(meta, "total_cells").text = str(len(memory))
        ET.SubElement(meta, "ranges_count").text = str(len(ranges))
        
        # Добавление данных памяти для каждого диапазона
        for i, (start, end) in enumerate(ranges):
            # Корректировка границ
            start = max(0, start)
            end = min(len(memory) - 1, end)
            
            range_elem = ET.SubElement(root, "range")
            range_elem.set("id", str(i))
            range_elem.set("start", str(start))
            range_elem.set("end", str(end))
            range_elem.set("size", str(end - start + 1))
            
            for addr in range(start, end + 1):
                cell = ET.SubElement(range_elem, "cell")
                cell.set("address", str(addr))
                cell.set("value", str(memory[addr]))
                cell.set("hex", f"0x{memory[addr]:X}")
        
        # Форматирование и сохранение XML
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        print(f"✅ Дамп памяти сохранен в {output_file}")
        
        # Показать краткий дамп
        print(f"\n📊 Краткий дамп (первые 2 диапазона):")
        for i, (start, end) in enumerate(ranges[:2]):
            print(f"\n  Диапазон {i+1}: {start}-{end}")
            for addr in range(start, min(start + 5, end + 1)):
                print(f"    [{addr:4}] = {memory[addr]:8} (0x{memory[addr]:X})")
            if end - start > 5:
                print(f"    ... ({end - start - 4} more cells)")
                
    except Exception as e:
        print(f"❌ Ошибка при сохранении дампа: {e}")

def create_test_program_max():
    """
    Создание тестовой программы для команды max()
    Проверяет различные случаи:
    1. max(10, 20) = 20
    2. max(-5, -10) = -5 (если поддерживаются отрицательные)
    3. max(100, 100) = 100 (равные значения)
    4. max(0, 0) = 0
    5. Работа с массивом
    """
    test_code = [
        '# ==========================================',
        '# Тестовая программа для команды MAX',
        '# ==========================================',
        '',
        '# 1. Базовый тест: max(10, 20) = 20',
        '{"op": "load_const", "address": 500, "constant": 10}',
        '{"op": "load_const", "address": 501, "constant": 20}',
        '{"op": "max", "addr_b": 500, "addr_c": 502, "addr_d": 501}',
        '',
        '# 2. max(50, 30) = 50',
        '{"op": "load_const", "address": 503, "constant": 50}',
        '{"op": "load_const", "address": 504, "constant": 30}',
        '{"op": "max", "addr_b": 503, "addr_c": 505, "addr_d": 504}',
        '',
        '# 3. max(100, 100) = 100 (равные значения)',
        '{"op": "load_const", "address": 506, "constant": 100}',
        '{"op": "load_const", "address": 507, "constant": 100}',
        '{"op": "max", "addr_b": 506, "addr_c": 508, "addr_d": 507}',
        '',
        '# 4. max(0, 0) = 0',
        '{"op": "load_const", "address": 509, "constant": 0}',
        '{"op": "load_const", "address": 510, "constant": 0}',
        '{"op": "max", "addr_b": 509, "addr_c": 511, "addr_d": 510}',
        '',
        '# 5. Работа с массивом: найти максимум в массиве из 5 элементов',
        '# Массив [15, 42, 7, 89, 23] по адресам 600-604',
        '{"op": "load_const", "address": 600, "constant": 15}',
        '{"op": "load_const", "address": 601, "constant": 42}',
        '{"op": "load_const", "address": 602, "constant": 7}',
        '{"op": "load_const", "address": 603, "constant": 89}',
        '{"op": "load_const", "address": 604, "constant": 23}',
        '',
        '# Поиск максимума: max(max(max(max(15,42),7),89),23)',
        '# Первое сравнение: max(15, 42) = 42 -> memory[610]',
        '{"op": "max", "addr_b": 600, "addr_c": 610, "addr_d": 601}',
        '# Второе: max(42, 7) = 42 -> memory[611]',
        '{"op": "max", "addr_b": 610, "addr_c": 611, "addr_d": 602}',
        '# Третье: max(42, 89) = 89 -> memory[612]',
        '{"op": "max", "addr_b": 611, "addr_c": 612, "addr_d": 603}',
        '# Четвертое: max(89, 23) = 89 -> memory[613] (итоговый максимум)',
        '{"op": "max", "addr_b": 612, "addr_c": 613, "addr_d": 604}',
        '',
        '# 6. Комплексный пример с чтением и записью',
        '{"op": "read", "dst_addr": 700, "src_addr": 613}  # Копируем максимум',
        '{"op": "write", "src_addr": 700, "offset": 5, "base_addr": 800}  # Сохраняем со смещением',
    ]
    
    return '\n'.join(test_code)

def create_test_program_max_vectors():
    """
    Создание тестовой программы для работы с векторами (массивами)
    Находит максимальные элементы в двух векторах и сохраняет результаты
    """
    test_code = [
        '# ==========================================',
        '# Тест: MAX для двух векторов длины 5',
        '# ==========================================',
        '',
        '# Вектор A: [5, 12, 8, 20, 3] по адресам 1000-1004',
        '{"op": "load_const", "address": 1000, "constant": 5}',
        '{"op": "load_const", "address": 1001, "constant": 12}',
        '{"op": "load_const", "address": 1002, "constant": 8}',
        '{"op": "load_const", "address": 1003, "constant": 20}',
        '{"op": "load_const", "address": 1004, "constant": 3}',
        '',
        '# Вектор B: [7, 10, 15, 18, 25] по адресам 1010-1014',
        '{"op": "load_const", "address": 1010, "constant": 7}',
        '{"op": "load_const", "address": 1011, "constant": 10}',
        '{"op": "load_const", "address": 1012, "constant": 15}',
        '{"op": "load_const", "address": 1013, "constant": 18}',
        '{"op": "load_const", "address": 1014, "constant": 25}',
        '',
        '# Результат: max(A[i], B[i]) по адресам 1020-1024',
        '{"op": "max", "addr_b": 1000, "addr_c": 1020, "addr_d": 1010}',
        '{"op": "max", "addr_b": 1001, "addr_c": 1021, "addr_d": 1011}',
        '{"op": "max", "addr_b": 1002, "addr_c": 1022, "addr_d": 1012}',
        '{"op": "max", "addr_b": 1003, "addr_c": 1023, "addr_d": 1013}',
        '{"op": "max", "addr_b": 1004, "addr_c": 1024, "addr_d": 1014}',
        '',
        '# Находим общий максимум из результатов',
        '# max(1020, 1021) -> 1030',
        '{"op": "max", "addr_b": 1020, "addr_c": 1030, "addr_d": 1021}',
        '# max(1030, 1022) -> 1031',
        '{"op": "max", "addr_b": 1030, "addr_c": 1031, "addr_d": 1022}',
        '# max(1031, 1023) -> 1032',
        '{"op": "max", "addr_b": 1031, "addr_c": 1032, "addr_d": 1023}',
        '# max(1032, 1024) -> 1033 (итоговый максимум)',
        '{"op": "max", "addr_b": 1032, "addr_c": 1033, "addr_d": 1024}',
    ]
    
    return '\n'.join(test_code)

def main():
    parser = argparse.ArgumentParser(
        description='Интерпретатор УВМ с поддержкой АЛУ (команда MAX) - Этап 4'
    )
    parser.add_argument('-i', '--input', required=False, 
                       help='Путь к бинарному файлу с программой')
    parser.add_argument('-o', '--output', required=False, 
                       help='Путь к файлу для сохранения дампа памяти')
    parser.add_argument('-r', '--range', required=False, 
                       help='Диапазон адресов для вывода дампа (например: "500-511,600-604")')
    parser.add_argument('--test-max', action='store_true',
                       help='Создать и выполнить тестовую программу для команды MAX')
    parser.add_argument('--test-vectors', action='store_true',
                       help='Создать тестовую программу для векторов')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Подробный вывод выполнения команд')
    
    args = parser.parse_args()
    
    # Если запрошен тест max
    if args.test_max:
        print("🧪 Создание тестовой программы для команды MAX...")
        
        # Создаем тестовую программу
        test_program = create_test_program_max()
        
        # Сохраняем ее
        with open('test_max.uvm', 'w', encoding='utf-8') as f:
            f.write(test_program)
        
        print("✅ Тестовая программа сохранена в test_max.uvm")
        print("\nДля выполнения:")
        print("1. Ассемблируйте: python uvm_asm.py -i test_max.uvm -o test_max.bin")
        print("2. Запустите: python uvm_interp.py -i test_max.bin -o max_dump.xml -r 500-511,600-604,610-613,700-700,800-805 -v")
        return
    
    # Если запрошен тест векторов
    if args.test_vectors:
        print("🧪 Создание тестовой программы для векторов...")
        
        # Создаем тестовую программу
        test_program = create_test_program_max_vectors()
        
        # Сохраняем ее
        with open('test_vectors.uvm', 'w', encoding='utf-8') as f:
            f.write(test_program)
        
        print("✅ Тестовая программа сохранена в test_vectors.uvm")
        print("\nДля выполнения:")
        print("1. Ассемблируйте: python uvm_asm.py -i test_vectors.uvm -o test_vectors.bin")
        print("2. Запустите: python uvm_interp.py -i test_vectors.bin -o vectors_dump.xml -r 1000-1004,1010-1014,1020-1024,1030-1033 -v")
        return
    
    # Основной режим работы
    if not all([args.input, args.output, args.range]):
        print("Использование:")
        print("  python uvm_interp.py -i input.bin -o output.xml -r range")
        print("  python uvm_interp.py --test-max           # Создать тест MAX")
        print("  python uvm_interp.py --test-vectors      # Создать тест векторов")
        print("  python uvm_interp.py -i file.bin -o dump.xml -r range -v  # Подробный вывод")
        return
    
    print("🚀 Запуск интерпретатора УВМ с поддержкой АЛУ")
    print("=" * 60)
    
    try:
        # Чтение байткода
        with open(args.input, "rb") as file:
            bytecode = file.read()
        
        print(f"📦 Загружен файл: {args.input}")
        print(f"   Размер: {len(bytecode)} байт")
        
        # Выполнение программы
        print("\n⚡ Выполнение программы с АЛУ операциями...")
        data_memory = execute_program(bytecode, data_memory_size=2048, verbose=args.verbose)
        
        # Сохранение дампа памяти
        print("\n💾 Сохранение дампа памяти...")
        save_xml_dump(data_memory, args.output, args.range)
        
        print("\n✅ Интерпретатор с АЛУ завершил работу успешно!")
        
    except FileNotFoundError:
        print(f"❌ Файл не найден: {args.input}")
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")

if __name__ == "__main__":
    main()