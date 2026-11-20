"""Installs the four MM9 spellbook ground models and binds them by icon (mm9_spellbook_<mastery>).

Per mastery: the winding check (0 inverted closed parts), tools/install_model.py --world-items --world mm9 (source
assets_source/worlds/mm9/world_items/models/item_mm9_spellbook_<mastery>.glb), and an entry in the MM9 ground-item
ledger (level_generation/props/items_mm9_claude/ledger.json) naming its icon and the books that use it; then that
project's install_mm9.py --bindings rewrites assets_dev/worlds/mm9/world_items/items.yml with every entry and
tools/item_model_shapes.py fills the bounds. Books are 50 units long, like every MM6-MM8 spellbook.
Usage: python3 -I install_models.py [mastery ...]"""
import csv
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
WINDING = os.path.join(REPO, 'level_generation', 'decorations', 'mm8_3d', 'animated', 'scripts', 'check_winding.py')
LEDGER_PROJECT = os.path.join(REPO, 'level_generation', 'props', 'items_mm9_claude')
ITEMS = os.path.join(REPO, 'assets_dev', 'worlds', 'mm9', 'data_tables', 'items.txt')
MASTERIES = ('normal', 'expert', 'master', 'grandmaster')
LENGTH = 50.0


def main():
    with open(ITEMS, encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    ledger_path = os.path.join(LEDGER_PROJECT, 'ledger.json')
    ledger = json.load(open(ledger_path))
    for mastery in sys.argv[1:] or MASTERIES:
        icon = f'mm9_spellbook_{mastery}'
        export = os.path.join(HERE, 'work', f'{icon}_export.glb')
        check = subprocess.run([sys.executable, WINDING, export], capture_output=True, text=True)
        print(check.stdout.strip())
        if check.returncode != 0 or 'inverted closed parts: 0' not in check.stdout:
            raise SystemExit(f'{icon}: winding check failed')
        name = f'item_{icon}.glb'
        subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'install_model.py'), export, '--world-items',
                        '--world', 'mm9', '--name', name], check=True, cwd=REPO)
        items = [int(row['Item #']) for row in rows if row['Pic File'] == icon]
        if not items:
            raise SystemExit(f'{icon}: no item uses it (run import_mm9_items.py first)')
        ledger[f'spellbook_{mastery}'] = {
            'route': 'blender', 'export': os.path.relpath(export, REPO),
            'sha256': hashlib.sha256(open(export, 'rb').read()).hexdigest(),
            'model': f'worlds/mm9/world_items/models/{name}', 'items': items, 'icons': [icon],
            'title': f'Spellbook ({mastery.capitalize()}): {len(items)} spells', 'length': LENGTH}
        print('installed', icon, len(items), 'books')
    with open(ledger_path, 'w') as handle:
        json.dump(ledger, handle, indent=1, sort_keys=True)
        handle.write('\n')
    subprocess.run([sys.executable, os.path.join(LEDGER_PROJECT, 'scripts', 'install_mm9.py'), '--bindings'],
                   check=True, cwd=REPO)


main()
