import re
import os

def extract_fa_icons(css_path):
    if not os.path.exists(css_path):
        return []

    with open(css_path, 'r') as f:
        css = f.read()

    # Find all `.fa-ICONNAME:before` entries
    icons = re.findall(r'\.fa-([a-z0-9\-]+):before', css)
    return sorted(set(icons))
