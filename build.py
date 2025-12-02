#!/usr/bin/env python3
"""
Сборка с веб-версией на Pyodide (Python в браузере)
"""

import os
import shutil
import json
from pathlib import Path

class UVMBuilder:
    def __init__(self):
        self.root = Path(__file__).parent
        self.dist = self.root / "dist"
    
    def clean(self):
        if self.dist.exists():
            shutil.rmtree(self.dist)
        self.dist.mkdir()
        print("✅ Очищено")
    
    def create_web_pyodide(self):
        """Веб-версия с Pyodide (Python в браузере)"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>УВМ - Python в браузере</title>
    <script type="text/javascript" src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    <style>
        body{font-family:Arial;margin:20px;background:#f5f5f5}
        .container{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}
        .panel{background:white;padding:15px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        textarea{width:100%;height:250px;font-family:monospace;padding:10px;border:1px solid #ddd}
        button{background:#0078D7;color:white;border:none;padding:8px 15px;margin:5px;border-radius:5px;cursor:pointer}
        .output{background:#1e1e1e;color:#d4d4d4;padding:10px;height:250px;overflow:auto;font-family:monospace;white-space:pre-wrap}
        .status{padding:10px;background:#e8f4fd;border-radius:5px;margin:10px 0}
        .memory-dump{background:#f9f9f9;padding:10px;height:250px;overflow:auto;font-family:monospace;white-space:pre-wrap;border:1px solid #ddd}
        .dump-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
        .dump-title{font-weight:bold;color:#333}
        .btn-small{background:#28a745;font-size:12px;padding:5px 10px}
        .btn-dump{background:#6f42c1;}
    </style>
</head>
<body>
    <h2>🐍 УВМ - Python в браузере</h2>
    <div class="status" id="status">Загрузка Python (Pyodide)...</div>
    
    <div class="container">
        <div class="panel">
            <h3>📝 Редактор программы</h3>
            <textarea id="editor">{"op":"load_const","address":100,"constant":42}
{"op":"read","dst_addr":200,"src_addr":100}
{"op":"max","addr_b":100,"addr_c":300,"addr_d":200}</textarea>
            <div>
                <button onclick="assemble()" id="asmBtn" disabled>▶ Ассемблировать</button>
                <button onclick="runTests()" id="testBtn" disabled>🧪 Тесты</button>
                <button onclick="executeAndDump()" id="dumpBtn" disabled class="btn-dump">💾 Выполнить и дамп</button>
            </div>
        </div>
        
        <div class="panel">
            <h3>📊 Результаты ассемблирования</h3>
            <div id="output" class="output">// Здесь будет результат</div>
        </div>
        
        <div class="panel">
            <div class="dump-header">
                <h3>🧠 Дамп памяти</h3>
                <button onclick="clearMemoryDump()" class="btn-small">Очистить</button>
            </div>
            <div id="memoryDump" class="memory-dump">
                // Здесь будет дамп памяти<br>
                // Нажмите "Выполнить и дамп"
            </div>
            <div style="margin-top:10px;">
                <label for="dumpRange">Диапазон адресов: </label>
                <input type="text" id="dumpRange" value="0-255" style="width:100px;">
                <button onclick="dumpMemoryRange()" class="btn-small">Дамп диапазона</button>
            </div>
        </div>
    </div>

    <script>
        let pyodide;
        let memory = new Array(65536).fill(0); // 64K памяти
        let bytecode = null;
        
        let pyCode = `
def mask(bits):
    return (1 << bits) - 1

def create_command(op_code, fields):
    command = 0
    command |= (op_code & mask(5))
    
    if op_code == 19:
        address = fields.get('address', 0)
        constant = fields.get('constant', 0)
        command |= (address & mask(16)) << 5
        command |= (constant & mask(20)) << 21
    elif op_code == 3:
        dst_addr = fields.get('dst_addr', 0)
        src_addr = fields.get('src_addr', 0)
        command |= (dst_addr & mask(16)) << 5
        command |= (src_addr & mask(16)) << 21
    elif op_code == 20:
        src_addr = fields.get('src_addr', 0)
        offset = fields.get('offset', 0)
        base_addr = fields.get('base_addr', 0)
        command |= (src_addr & mask(16)) << 5
        command |= (offset & mask(5)) << 21
        command |= (base_addr & mask(16)) << 26
    elif op_code == 7:
        addr_b = fields.get('addr_b', 0)
        addr_c = fields.get('addr_c', 0)
        addr_d = fields.get('addr_d', 0)
        command |= (addr_b & mask(16)) << 5
        command |= (addr_c & mask(16)) << 21
        command |= (addr_d & mask(16)) << 37
    
    return command.to_bytes(7, 'little')

def assemble_text(text):
    import json
    bytecode = b''
    
    for line in text.split('\\\\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            cmd = json.loads(line)
            op = cmd['op']
            
            if op == 'load_const':
                bytecode += create_command(19, {'address': cmd['address'], 'constant': cmd['constant']})
            elif op == 'read':
                bytecode += create_command(3, {'dst_addr': cmd['dst_addr'], 'src_addr': cmd['src_addr']})
            elif op == 'write':
                bytecode += create_command(20, {'src_addr': cmd['src_addr'], 'offset': cmd['offset'], 'base_addr': cmd['base_addr']})
            elif op == 'max':
                bytecode += create_command(7, {'addr_b': cmd['addr_b'], 'addr_c': cmd['addr_c'], 'addr_d': cmd['addr_d']})
        except Exception as e:
            return f"Ошибка: {e}", b''
    
    result = "✅ Ассемблировано!\\\\n"
    result += f"Размер: {len(bytecode)} байт\\\\n\\\\n"
    
    for i in range(0, len(bytecode), 7):
        chunk = bytecode[i:i+7]
        hex_bytes = [f'0x{b:02X}' for b in chunk]
        result += f"Команда {i//7}: {', '.join(hex_bytes)}\\\\n"
    
    return result, bytecode

def execute_bytecode(bytecode_hex, memory_state):
    import struct
    
    # Конвертируем hex строку обратно в bytes
    bytecode = bytes.fromhex(bytecode_hex)
    
    # Инициализируем память из переданного состояния
    memory = memory_state.copy()
    
    operations = []
    
    # Выполняем команды
    for i in range(0, len(bytecode), 7):
        cmd_bytes = bytecode[i:i+7]
        if len(cmd_bytes) < 7:
            continue
            
        # Разбираем команду
        cmd_int = int.from_bytes(cmd_bytes, 'little')
        op_code = cmd_int & 0x1F
        
        if op_code == 19:  # load_const
            address = (cmd_int >> 5) & 0xFFFF
            constant = (cmd_int >> 21) & 0xFFFFF
            if address < len(memory):
                memory[address] = constant
                operations.append(f"Загружено {constant} в адрес {address}")
        
        elif op_code == 3:  # read
            dst_addr = (cmd_int >> 5) & 0xFFFF
            src_addr = (cmd_int >> 21) & 0xFFFF
            if src_addr < len(memory) and dst_addr < len(memory):
                memory[dst_addr] = memory[src_addr]
                operations.append(f"Скопировано из {src_addr} в {dst_addr}")
        
        elif op_code == 7:  # max
            addr_b = (cmd_int >> 5) & 0xFFFF
            addr_c = (cmd_int >> 21) & 0xFFFF
            addr_d = (cmd_int >> 37) & 0xFFFF
            
            if addr_b < len(memory) and addr_c < len(memory) and addr_d < len(memory):
                max_val = max(memory[addr_b], memory[addr_c])
                memory[addr_d] = max_val
                operations.append(f"MAX({memory[addr_b]}, {memory[addr_c]}) = {max_val} в {addr_d}")
    
    return memory, operations

def get_memory_dump(memory, start=0, end=255):
    result = ""
    for i in range(start, min(end + 1, len(memory)), 16):
        line = f"{i:04X}: "
        for j in range(16):
            addr = i + j
            if addr <= end and addr < len(memory):
                line += f"{memory[addr]:04X} "
            else:
                line += "     "
        result += line + "\\\\n"
    return result

def test_spec():
    tests = [
        ("load_const(825, 559)", create_command(19, {'address': 825, 'constant': 559})),
        ("read(84, 215)", create_command(3, {'dst_addr': 84, 'src_addr': 215})),
        ("write(193, 30, 352)", create_command(20, {'src_addr': 193, 'offset': 30, 'base_addr': 352})),
        ("max(782, 367, 565)", create_command(7, {'addr_b': 782, 'addr_c': 367, 'addr_d': 565}))
    ]
    
    expected = [
        b'\\\\x33\\\\x67\\\\xe0\\\\x45\\\\x00\\\\x00\\\\x00',
        b'\\\\x83\\\\x0a\\\\xe0\\\\x1a\\\\x00\\\\x00\\\\x00',
        b'\\\\x34\\\\x18\\\\xc0\\\\x83\\\\x05\\\\x00\\\\x00',
        b'\\\\x07\\\\x61\\\\x80\\\\x0d\\\\xa0\\\\xb6\\\\xa0'
    ]
    
    result = "🧪 Тесты спецификации:\\\\n"
    for (name, actual), exp in zip(tests, expected):
        if actual == exp:
            result += f"✅ {name}: OK\\\\n"
        else:
            hex_act = ' '.join(f'{b:02X}' for b in actual)
            hex_exp = ' '.join(f'{b:02X}' for b in exp)
            result += f"❌ {name}: {hex_act} (ожидалось {hex_exp})\\\\n"
    
    return result
`;

        async function main() {
            document.getElementById('status').innerHTML = '🚀 Загрузка Python...';
            
            try {
                // Загружаем Pyodide
                pyodide = await loadPyodide({
                    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
                });
                
                // Загружаем наш Python код
                await pyodide.runPythonAsync(pyCode);
                
                document.getElementById('status').innerHTML = '✅ Python загружен! Можно работать.';
                document.getElementById('asmBtn').disabled = false;
                document.getElementById('testBtn').disabled = false;
                document.getElementById('dumpBtn').disabled = false;
                
            } catch (error) {
                document.getElementById('status').innerHTML = `❌ Ошибка: ${error}`;
            }
        }

        async function assemble() {
            const code = document.getElementById('editor').value;
            document.getElementById('status').innerHTML = '⚙ Ассемблирование...';
            
            try {
                // Запускаем Python функцию
                const result = await pyodide.runPythonAsync(`assemble_text("""${code}""")`);
                const [text, bc] = result;
                bytecode = bc;
                document.getElementById('output').textContent = text;
                document.getElementById('status').innerHTML = '✅ Готово!';
            } catch (error) {
                document.getElementById('output').textContent = `Ошибка: ${error}`;
                document.getElementById('status').innerHTML = '❌ Ошибка ассемблирования';
            }
        }

        async function executeAndDump() {
            if (!bytecode) {
                alert('Сначала скомпилируйте программу!');
                return;
            }
            
            document.getElementById('status').innerHTML = '⚡ Выполнение и дамп памяти...';
            
            try {
                // Конвертируем bytecode в hex для передачи в Python
                const bytecodeHex = Array.from(new Uint8Array(bytecode)).map(b => b.toString(16).padStart(2, '0')).join('');
                
                // Выполняем программу
                const result = await pyodide.runPythonAsync(`
memory, ops = execute_bytecode("${bytecodeHex}", ${JSON.stringify(memory)})
dump = get_memory_dump(memory, 0, 255)
ops_text = "\\\\n".join(ops) if ops else "Нет операций записи"
(dump, ops_text, memory)
`);
                
                // Обновляем глобальное состояние памяти
                memory = result[2];
                
                // Показываем дамп
                const dumpText = result[0];
                const opsText = result[1];
                
                document.getElementById('memoryDump').innerHTML = 
                    `<span style="color:#28a745">Выполненные операции:</span><br>${opsText}<br><br>` +
                    `<span style="color:#0078D7">Дамп памяти (0-255):</span><br><pre>${dumpText}</pre>`;
                
                document.getElementById('status').innerHTML = '✅ Выполнение завершено!';
                
            } catch (error) {
                document.getElementById('memoryDump').innerHTML = `Ошибка выполнения: ${error}`;
                document.getElementById('status').innerHTML = '❌ Ошибка выполнения';
            }
        }

        async function dumpMemoryRange() {
            const rangeInput = document.getElementById('dumpRange').value;
            let start = 0, end = 255;
            
            try {
                const parts = rangeInput.split('-');
                if (parts.length === 2) {
                    start = parseInt(parts[0]);
                    end = parseInt(parts[1]);
                } else if (parts.length === 1) {
                    end = parseInt(parts[0]);
                }
            } catch (e) {
                alert('Неверный формат диапазона. Используйте "0-255"');
                return;
            }
            
            if (isNaN(start) || isNaN(end) || start < 0 || end >= memory.length || start > end) {
                alert('Неверный диапазон адресов');
                return;
            }
            
            document.getElementById('status').innerHTML = `📊 Дамп памяти ${start}-${end}...`;
            
            try {
                const dump = await pyodide.runPythonAsync(`get_memory_dump(${JSON.stringify(memory)}, ${start}, ${end})`);
                document.getElementById('memoryDump').innerHTML = 
                    `<span style="color:#0078D7">Дамп памяти (${start}-${end}):</span><br><pre>${dump}</pre>`;
                document.getElementById('status').innerHTML = '✅ Дамп готов!';
            } catch (error) {
                document.getElementById('memoryDump').innerHTML = `Ошибка дампа: ${error}`;
            }
        }

        function clearMemoryDump() {
            document.getElementById('memoryDump').innerHTML = 
                '// Дамп памяти очищен<br>' +
                '// Нажмите "Выполнить и дамп" для получения нового дампа';
            document.getElementById('status').innerHTML = '🧹 Дамп памяти очищен';
        }

        async function runTests() {
            document.getElementById('status').innerHTML = '🧪 Запуск тестов...';
            
            try {
                const result = await pyodide.runPythonAsync(`test_spec()`);
                document.getElementById('output').textContent = result;
                document.getElementById('status').innerHTML = '✅ Тесты завершены';
            } catch (error) {
                document.getElementById('output').textContent = `Ошибка: ${error}`;
            }
        }

        // Запускаем Pyodide при загрузке
        main();
    </script>
</body>
</html>'''
        
        web_dir = self.dist / "web"
        web_dir.mkdir(exist_ok=True)
        
        with open(web_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        print("✅ Веб-версия с Pyodide создана")
    
    def copy_python_files(self):
        """Копируем Python файлы"""
        files_to_copy = [
            ("uvm_asm.py", "uvm_asm.py"),
            ("uvm_interp.py", "uvm_interp.py"),
            ("uvm_gui.py", "uvm_gui.py"),
            ("README.txt", "README.txt"),
            ("test_spec_format.uvm", "examples/test_spec.uvm"),
        ]
        
        for src_name, dst_name in files_to_copy:
            src = self.root / src_name
            if src.exists():
                shutil.copy2(src, self.dist / dst_name)
                print(f"  📄 {dst_name}")
    
    def build_all(self):
        """Сборка всех версий"""
        print("🔨 Сборка УВМ...")
        self.clean()
        self.create_web_pyodide()
        self.copy_python_files() 
        
        print("\n✅ Готово!")
        print("📁 Файлы в папке dist/")
        print("🌐 Веб-версия: dist/web/index.html")
        print("💻 GUI: python uvm_gui.py")
        print("\n🚀 Веб-версия использует реальный Python в браузере!")
        print("💾 Добавлена возможность дампа памяти!")

if __name__ == "__main__":
    UVMBuilder().build_all()
