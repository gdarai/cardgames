import sys
import os
import json
import re
import subprocess
import shutil
from PIL import Image

# Default config
config = {
    'separator': '|',
    'fonts': {},
    'builds': {},
    'intermediate': '_intermediate.png'
}

def logBlock(msg):
    print(f"\n== {msg} ==")

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
    if 'intermediate' in task:
        config['intermediate'] = task['intermediate']
        log(f"Intermediate file set to '{config['intermediate']}'")
    else:
        log("No intermediate specified, using default")

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

def parse_build(task):
    log(f"Registering build: {task.get('name', '[no name]')}")
    required = ['name', 'elements']
    for r in required:
        if r not in task:
            error(f"BUILD task missing required field: {r}")
            return
    config['builds'][task['name']] = task['elements']
    log(f"Build '{task['name']}' registered with {len(task['elements'])} elements.")

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
    first_is_name = task.get('firstIsName', False)
    font_fill = str(font['fill'])
    font_source = str(font['source'])
    font_pointsize = int(font['pointSize'])
    font_rowheight = int(font['rowHeight'])
    font_gravity = str(task.get('gravity', 'Center'))
    font_vert = 0
    font_row_step = font_rowheight
    if 'North' in font_gravity:
        font_vert = -1
    elif 'South' in font_gravity:
        font_vert = 1
        font_row_step = -font_rowheight
    # Subset logic
    subset = task.get('subset', None)
    with open(source_path, encoding='utf-8') as f:
        lines = [line.strip('\n').strip('\r') for line in f if line.strip()]  # skip empty lines
    if subset:
        try:
            fromto = subset.split(':')
            from_idx = int(fromto[0]) if fromto[0] else None
            to_idx = int(fromto[1]) if len(fromto) > 1 and fromto[1] else None
            total = len(lines)
            # Handle negative indices
            from_idx = from_idx if from_idx is not None else 0
            to_idx = to_idx if to_idx is not None else total
            if from_idx < 0:
                from_idx = total + from_idx
            if to_idx < 0:
                to_idx = total + to_idx
            lines = lines[from_idx:to_idx]
        except Exception as e:
            error(f"Invalid subset parameter: {subset} ({e})")
    for idx, line in enumerate(lines):
        parts = [p.strip() for p in line.split(sep)]
        if first_is_name:
            if len(parts) < 2:
                error(f"Line {idx+1} in {source_path} does not have enough parts for firstIsName.")
                continue
            output_file = os.path.join(base_dir, f"{base_name}_{parts[0]}.png")
            text_parts = parts[1:]
        else:
            output_file = os.path.join(base_dir, f"{base_name}_{idx+1}.png")
            text_parts = parts
        annotates = []
        y_offset = 0
        if font_vert == 0:
            y_offset = -(len(text_parts)-1)*font_rowheight//2
        if font_vert == 1:
            y_offset = (len(text_parts)-1)*font_rowheight
        for i, part in enumerate(text_parts):
            offset = y_offset + i*font_row_step
            annotates.extend(['-annotate', f'+0+{offset}', part])
        cmd = [
            'convert',
            '-size', *size_args,
            '-gravity', font_gravity,
            '-fill', font_fill,
            '-font', font_source,
            '-pointsize', str(font_pointsize)
        ] + annotates + [output_file]
        log(f"Creating image: {output_file}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            error(f"ImageMagick convert failed for {output_file}: {e}")

def parse_cards(task):
    log(f"Processing CARDS task: {task.get('source', '[no source]')}")
    required = ['source', 'base', 'target', 'build']
    for r in required:
        if r not in task:
            error(f"CARDS task missing required field: {r}")
            return
    txt_source = task['source']
    base_img = task['base']
    target = task['target']
    build_name = task['build']
    crop_str = task.get('crop', None)
    print_limit = task.get('printLimit', -1)
    first_is_name = task.get('firstIsName', False)
    subset = task.get('subset', None)
    if build_name not in config['builds']:
        error(f"Build '{build_name}' not registered.")
        return
    build_elements = config['builds'][build_name]
    sep = config.get('separator', '|')
    if not check_file_exists(txt_source):
        return
    size_match = re.match(r'^(\d+)x(\d+)$', str(base_img))
    if size_match:
        width, height = int(size_match.group(1)), int(size_match.group(2))
        base_img_path = f'_base_image_{width}x{height}.png'
        if not os.path.isfile(base_img_path):
            img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            img.save(base_img_path)
        base_img = base_img_path
    if not check_file_exists(base_img):
        return
    os.makedirs(os.path.dirname(target), exist_ok=True)
    # Subset logic
    with open(txt_source, encoding='utf-8') as f:
        lines = [line.strip('\n').strip('\r') for line in f if line.strip()]
    if subset:
        try:
            fromto = subset.split(':')
            from_idx = int(fromto[0]) if fromto[0] else None
            to_idx = int(fromto[1]) if len(fromto) > 1 and fromto[1] else None
            total = len(lines)
            from_idx = from_idx if from_idx is not None else 0
            to_idx = to_idx if to_idx is not None else total
            if from_idx < 0:
                from_idx = total + from_idx
            if to_idx < 0:
                to_idx = total + to_idx
            lines = lines[from_idx:to_idx]
        except Exception as e:
            error(f"Invalid subset parameter: {subset} ({e})")
    for idx, line in enumerate(lines):
        if 0 < print_limit <= idx:
            log(f"Print limit reached ({print_limit}), stopping.")
            break
        values = [p.strip() for p in line.split(sep)]
        # Determine output file name and values for placeholders
        if first_is_name:
            if len(values) < 2:
                error(f"Line {idx+1} in {txt_source} does not have enough parts for firstIsName.")
                continue
            output_file = f"{target}_{values[0]}.png"
            values_for_build = values[1:]
        else:
            output_file = f"{target}_{idx+1}.png"
            values_for_build = values
        # Start with base image
        current_img = base_img
        for el_idx, element in enumerate(build_elements):
            src_template = element['source']
            skip_print = False
            # Replace placeholders [0], [1], ...
            src_img = src_template
            src_mem = src_img
            for i, val in enumerate(values_for_build):
                src_img = src_img.replace(f'[{i}]', val)
                if src_mem != src_img and val == '':
                    skip_print = True
                    log(f"Element source results in empty string, skipping element {el_idx+1} for line {idx+1}")
                    continue
                src_mem = src_img
            if not skip_print and not check_file_exists(src_img):
                error(f"Element source not found: {src_img}")
                continue
            if skip_print:
                continue
            position = element.get('position', '+0+0')
            centered = element.get('centered', False)
            geometry = position
            if centered:
                # Get overlay size
                try:
                    with Image.open(src_img) as im:
                        w, h = im.size
                    # Parse position
                    m = re.match(r'([+-]?\d+)([+-]\d+)', position)
                    if m:
                        x = int(m.group(1))
                        y = int(m.group(2))
                        x -= w // 2
                        y -= h // 2
                        geometry = f'+{x}+{y}' if x >= 0 and y >= 0 else f'{x:+d}{y:+d}'
                except Exception as e:
                    error(f"Failed to get image size for centering: {src_img}: {e}")
            # Compose images
            interm = config['intermediate']
            cmd = [
                'convert', current_img, src_img, '-geometry', geometry, '-composite', interm
            ]
            log(f"Compositing: {current_img} + {src_img} at {geometry} -> {interm}")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                error(f"ImageMagick composite failed: {e}")
                break
            current_img = interm
        # Save final result
        if crop_str:
            crop_cmd = [
                'convert', current_img, '-crop', crop_str, output_file
            ]
            log(f"Cropping image: {current_img} with crop '{crop_str}' -> {output_file}")
            try:
                subprocess.run(crop_cmd, check=True)
            except subprocess.CalledProcessError as e:
                error(f"ImageMagick crop failed: {e}")
                shutil.copy(current_img, output_file)
        else:
            shutil.copy(current_img, output_file)
        log(f"Created card: {output_file}")

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

    logBlock('Welcome to FinePrint')
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
            logBlock('SETUP - change settings')
            parse_setup(task)
        elif ttype == 'FONT':
            logBlock('FONT - register font')
            parse_font(task)
        elif ttype == 'BUILD':
            logBlock('BUILD - register img build')
            parse_build(task)
        elif ttype == 'TEXTS':
            logBlock('TEXTS - printing texts to imgs')
            parse_texts(task)
        elif ttype == 'CARDS':
            logBlock('CARDS - assembling cards')
            parse_cards(task)
        elif ttype == 'CLEAN':
            logBlock('CLEAN - cleaning workspace')
            parse_clean(task)
        else:
            error(f"Unknown task type: {ttype}")
    # Delete the intermediate file if it exists
    interm_file = config.get('intermediate', '_intermediate.png')
    if os.path.exists(interm_file):
        logBlock('Final cleanup')
        try:
            os.remove(interm_file)
            log(f"Deleted intermediate file: {interm_file}")
        except Exception as e:
            error(f"Failed to delete intermediate file {interm_file}: {e}")

if __name__ == '__main__':
    main()
