import glob
import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    changed = False
    for line in lines:
        new_lines.append(line)
        if 'img_b64 = base64.b64encode(' in line:
            indent = line[:len(line) - len(line.lstrip())]
            match = re.search(r'code\.append\([\'\"](\s*)img_b64 =', line)
            if match:
                inner_indent = match.group(1)
                quote_char = line[line.find('code.append(') + 12]
                new_lines.append(f'{indent}code.append({quote_char}{inner_indent}if \\\'register_figure\\\' in globals():{quote_char})\n')
                new_lines.append(f'{indent}code.append({quote_char}{inner_indent}    register_figure(img_b64, fig){quote_char})\n')
                changed = True
            else:
                match = re.search(r'^(\s*)[\'\"](\s*)img_b64 = base64\.b64encode', line)
                if match:
                    outer_indent = match.group(1)
                    quote_char = line[len(outer_indent)]
                    inner_indent = match.group(2)
                    new_lines.append(f'{outer_indent}{quote_char}{inner_indent}if \\\'register_figure\\\' in globals():{quote_char},\n')
                    new_lines.append(f'{outer_indent}{quote_char}{inner_indent}    register_figure(img_b64, fig){quote_char},\n')
                    changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f'Updated {os.path.basename(filepath)}')

for f in glob.glob('src/quantia/ui/dialogs/*.py'):
    process_file(f)
