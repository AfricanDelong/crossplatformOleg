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
        .container{display:grid;grid-template-columns:1fr 1fr;gap:20px}
        .panel{background:white;padding:15px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        textarea{width:100%;height:250px;font-family:monospace;padding:10px;border:1px solid #ddd}
        button{background:#0078D7;color:white;border:none;padding:8px 15px;margin:5px;border-radius:5px;cursor:pointer}
        .output{background:#1e1e1e;color:#d4d4d4;padding:10px;height:250px;overflow:auto;font-family:monospace;white-space:pre-wrap}
        .status{padding:10px;background:#e8f4fd;border-radius:5px;margin:10px 0}
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
            </div>
        </div>
        
        <div class="panel">
            <h3>📊 Результаты ассемблирования</h3>
            <div id="output" class="output">// Здесь будет результат</div>
        </div>
    </div>

    <script>
        let pyodide;
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
            return f"Ошибка: {e}"
    
    result = "✅ Ассемблировано!\\\\n"
    result += f"Размер: {len(bytecode)} байт\\\\n\\\\n"
    
    for i in range(0, len(bytecode), 7):
        chunk = bytecode[i:i+7]
        hex_bytes = [f'0x{b:02X}' for b in chunk]
        result += f"Команда {i//7}: {', '.join(hex_bytes)}\\\\n"
    
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
                document.getElementById('output').textContent = result;
                document.getElementById('status').innerHTML = '✅ Готово!';
            } catch (error) {
                document.getElementById('output').textContent = `Ошибка: ${error}`;
                document.getElementById('status').innerHTML = '❌ Ошибка ассемблирования';
            }
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

if __name__ == "__main__":
    UVMBuilder().build_all()
