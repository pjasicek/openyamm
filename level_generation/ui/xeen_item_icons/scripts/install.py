"""Installs accepted icons and points their item rows at them.

    python3 -I install.py <key> ...      copy items/<file>/icon_a_x2.png to assets_dev/worlds/xeen/icons_x2/<file>.png
                                         (0644) and replace the key's `icon_needed: ...` in source/items.yml with
                                         `icon: <file>`
    python3 -I install.py --grips        weapons with an installed icon: the paper-doll grip (items.txt Equip X/Y) by
                                         tools/mm9_import_discovery/generate_mm9_item_equipment_visuals.py's
                                         reference transfer, written as `grip: [x, y]` beside the key's icon

Accepted keys are listed in accepted.yml (candidate per key). Rerun tools/xeen/build_world.py after either step.
"""
import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
WORLD = REPO / 'assets_dev/worlds/xeen'
ITEMS_YML = WORLD / 'source/items.yml'
ICONS = WORLD / 'icons_x2'


def manifest():
    return {t['key']: t for t in yaml.safe_load(open(HERE / 'manifest.yml'))['targets']}


def entry_span(text, key):
    """The text of `  <key>: ...` up to the next entry at the same indent (or a blank line / section)."""
    match = re.search(rf'^(  ){re.escape(key)}:', text, re.M)
    if match is None:
        raise SystemExit(f'{key}: not in items.yml')
    rest_start = text.find('\n', match.end()) + 1
    end = re.search(r'^(  \S|\S|\s*$)', text[rest_start:], re.M)
    return match.start(), rest_start + (end.start() if end else len(text) - rest_start)


def install(keys):
    targets = manifest()
    accepted = yaml.safe_load(open(HERE / 'accepted.yml')) or {}
    text = ITEMS_YML.read_text()
    ICONS.mkdir(exist_ok=True)
    for key in keys:
        target = targets[key]
        candidate = accepted.get(key)
        if candidate is None:
            raise SystemExit(f'{key}: not accepted (accepted.yml)')
        source = HERE / 'items' / target['file'] / f'icon_{candidate}_x2.png'
        destination = ICONS / f"{target['file']}.png"
        shutil.copyfile(source, destination)
        os.chmod(destination, 0o644)
        start, end = entry_span(text, key)
        block = text[start:end]
        new = re.sub(r'icon_needed: (".*?"|[^,}\n]*)', f"icon: {target['file']}", block, count=1, flags=re.S)
        if new == block and f"icon: {target['file']}" not in block:
            raise SystemExit(f'{key}: no icon_needed field to replace')
        text = text[:start] + new + text[end:]
        print(key, '->', destination.relative_to(REPO))
    ITEMS_YML.write_text(text)


def load_grip_tool():
    path = REPO / 'tools/mm9_import_discovery/generate_mm9_item_equipment_visuals.py'
    spec = importlib.util.spec_from_file_location('grip_tool', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['grip_tool'] = module  # dataclasses look their module up
    spec.loader.exec_module(module)
    return module


def grips():
    tool = load_grip_tool()
    items = tool.read_items(WORLD / 'data_tables/items.txt', False)
    engine = tool.read_items(REPO / 'assets_dev/engine/data_tables/items.txt', False)
    by_file = {}
    for item in items.values():
        if item.equip_stat in {'Weapon', 'Weapon2', 'Weapon1or2', 'Missile'} and item.icon_name.startswith('xeen_item_'):
            by_file.setdefault(item.icon_name, item)
    files = {t['file']: key for key, t in manifest().items()}
    text = ITEMS_YML.read_text()
    for file, item in sorted(by_file.items()):
        icon = tool.find_icon(ICONS, file)
        mask = tool.item_mask(icon)
        reference, reference_mask = tool.nearest_reference(item, mask, engine, REPO / 'assets_dev/engine/icons_x2')
        anchor = tool.derive_anchor(item, mask, reference, reference_mask)
        key = files[file]
        start, end = entry_span(text, key)
        block = text[start:end]
        block = re.sub(r', grip: \[\d+, \d+\]|\n\s+grip: \[\d+, \d+\]', '', block)
        line = re.search(rf'^(\s+)icon: {file}$', block, re.M)
        if line:  # block style: a line of its own
            block = block[:line.end()] + f'\n{line.group(1)}grip: [{anchor[0]}, {anchor[1]}]' + block[line.end():]
        else:
            block = block.replace(f'icon: {file}', f'icon: {file}, grip: [{anchor[0]}, {anchor[1]}]', 1)
        text = text[:start] + block + text[end:]
        print(key, file, 'grip', anchor, 'from', reference.item_id, reference.name, (item.equip_x, item.equip_y))
    ITEMS_YML.write_text(text)


if __name__ == '__main__':
    if sys.argv[1:] == ['--grips']:
        grips()
    else:
        install(sys.argv[1:])
