import os
import re

files = [
    'src/quantia/ui/dialogs/regression.py',
    'src/quantia/ui/dialogs/logistic_regression.py',
    'src/quantia/ui/dialogs/classification.py'
]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace show_plotly(...) with html_output += ...
    pattern = r"show_plotly\([^,]+,\s*(fig_[a-zA-Z0-9_]+)\.to_html\(include_plotlyjs='cdn'\)\)"
    replacement = r"html_output += f'<div style=\"margin-top:24px; text-align:center;\">{{\1.to_html(include_plotlyjs=\"cdn\", full_html=False)}}</div>'"
    
    new_content = re.sub(pattern, replacement, content)
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Updated {fpath}')
