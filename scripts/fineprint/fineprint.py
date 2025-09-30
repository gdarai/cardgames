import sys
import os
import json
import re
import subprocess
import shutil  # Added for CLEAN task

# Default config
config = {
    'separator': '|',
    'fonts': {}
}

def log(msg):
    print(f"[INFO] {msg}")

def error(msg):
    print(f"[ERROR] {msg}")

def check_file_exists(path):
    if not os.path.isfile(path):
        error(f"File not found: {path}")
        return False
    return True

def parse_setup(task):
    log("Processing SETUP task")
    if 'separator' in task:
        config['separator'] = task['separator']
        log(f"Separator set to '{config['separator']}'")
    else:
        log("No separator specified, using default")

def parse_font(task):
    log(f"Registering font: {task.get('name', '[no name]')}")
    required = ['name', 'source', 'fill', 'pointSize', 'rowHeight']
    for r in required:
        if r not in task:
            error(f"FONT task missing required field: {r}")
            return
    font_path = task['source']
    if not font_path.startswith('/'):
        font_path = '/' + font_path
    if not check_file_exists(font_path):
        return
    config['fonts'][task['name']] = {
        'source': font_path,
        'fill': task['fill'],
        'pointSize': int(task['pointSize']),
        'rowHeight': int(task['rowHeight'])
    }
    log(f"Font '{task['name']}' registered.")

def parse_texts(task):
    log(f"Processing TEXTS task: {task.get('source', '[no source]')}")
    required = ['source', 'target', 'font', 'size']
    for r in required:
        if r not in task:
            error(f"TEXTS task missing required field: {r}")
            return
    font_name = task['font']
    if font_name not in config['fonts']:
        error(f"Font '{font_name}' not registered.")
        return
    font = config['fonts'][font_name]
    source_path = task['source']
    if not check_file_exists(source_path):
        return
    target_dir = task['target']
    base_dir = os.path.dirname(target_dir)
    base_name = os.path.basename(target_dir)

    os.makedirs(base_dir, exist_ok=True)
    sep = config.get('separator', '|')
    size = task['size']
    size_args = re.split(r'\s+', size.strip())
    with open(source_path, encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip('\n').strip('\r')
            if not line:
                continue
            parts = [p.strip() for p in line.split(sep)]
            annotates = []
            y_offset = -(len(parts)-1)*font['rowHeight']//2
            for i, part in enumerate(parts):
                offset = y_offset + i*font['rowHeight']
                annotates.extend(['-annotate', f'+0+{offset}', part])
            output_file = os.path.join(base_dir, f"{base_name}_{idx+1}.png")
            cmd = [
                'convert',
                '-size', *size_args,
                '-gravity', 'center',
                '-fill', font['fill'],
                '-font', font['source'],
                '-pointsize', str(font['pointSize'])
            ] + annotates + [output_file]
            log(f"Creating image: {output_file}")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                error(f"ImageMagick convert failed for {output_file}: {e}")

def parse_clean(task):
    log(f"Processing CLEAN task: {task.get('target', '[no target]')}")
    if 'target' not in task:
        error("CLEAN task missing required field: target")
        return
    target_dir = task['target']
    if not os.path.exists(target_dir):
        log(f"Target directory does not exist: {target_dir}")
        return
    if not os.path.isdir(target_dir):
        error(f"Target is not a directory: {target_dir}")
        return
    try:
        shutil.rmtree(target_dir)
        log(f"Deleted directory and all contents: {target_dir}")
    except Exception as e:
        error(f"Failed to delete directory {target_dir}: {e}")

def main():
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = 'guide.json'
    log(f"Using input file: {json_path}")
    if not check_file_exists(json_path):
        sys.exit(1)
    with open(json_path, encoding='utf-8') as f:
        try:
            tasks = json.load(f)
        except Exception as e:
            error(f"Failed to parse JSON: {e}")
            sys.exit(1)
    if not isinstance(tasks, list):
        error("Input JSON must be an array of tasks.")
        sys.exit(1)
    for task in tasks:
        if not isinstance(task, dict) or 'task' not in task:
            error("Each task must be an object with a 'task' field.")
            continue
        ttype = task['task']
        if ttype == 'SETUP':
            parse_setup(task)
        elif ttype == 'FONT':
            parse_font(task)
        elif ttype == 'TEXTS':
            parse_texts(task)
        elif ttype == 'CLEAN':
            parse_clean(task)
        else:
            error(f"Unknown task type: {ttype}")

if __name__ == '__main__':
    main()
