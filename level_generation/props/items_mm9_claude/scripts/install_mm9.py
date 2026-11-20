"""Installs reviewed MM9 ground-item models and writes MM9's own bindings.

Per design: the winding check (0 inverted closed parts), then tools/install_model.py --world-items --world mm9 (source
assets_source/worlds/mm9/world_items/models/item_mm9_<design id>.glb, cooked runtime copy in assets_dev) and its line in
ledger.json. Then assets_dev/worlds/mm9/world_items/items.yml is rewritten from the ledger: one binding per MM9 item of
every installed design (all items of a design share its model), and tools/item_model_shapes.py fills the bounds.
Usage: python3 scripts/install_mm9.py <design> [...]    (without -I: the installer and cook import sibling modules)
       python3 scripts/install_mm9.py --bindings        (rewrite the bindings from the ledger only)"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
WINDING = os.path.join(REPO, 'level_generation', 'decorations', 'mm8_3d', 'animated', 'scripts', 'check_winding.py')
BINDINGS = os.path.join(REPO, 'assets_dev', 'worlds', 'mm9', 'world_items', 'items.yml')
MODELS = 'worlds/mm9/world_items/models'
HEADER = """# MM9's own items lying on the ground in 3D, by inventory icon (items.txt "Pic File"), added to the engine's
# engine/world_items/items.yml (GameDataLoader; an icon bound in both fails). Items sharing a design share its model.
# Written by level_generation/props/items_mm9_claude/scripts/install_mm9.py; bounds by tools/item_model_shapes.py.
# length: world units of the model's longest horizontal side; see devdocs/GROUND_ITEMS_3D_PLAN.md.
schema: openyamm.itemModels.v1
items:
"""


def sha256(path):
    with open(path, 'rb') as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def install(design, ledger):
    export = os.path.join(HERE, 'work', 'codex_tex', f'{design}_export.glb')
    check = subprocess.run([sys.executable, WINDING, export], capture_output=True, text=True)
    print(check.stdout.strip())
    if check.returncode != 0 or 'inverted closed parts: 0' not in check.stdout:
        raise SystemExit(f'{design}: winding check failed')
    name = f"item_mm9_{design[1:]}.glb"
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'install_model.py'), export, '--world-items',
                    '--world', 'mm9', '--name', name], check=True, cwd=REPO)
    ledger[design] = {'route': DESIGNS[design]['route'], 'export': os.path.relpath(export, REPO),
                      'sha256': sha256(export), 'model': f'{MODELS}/{name}', 'items': DESIGNS[design]['items'],
                      'length': DESIGNS[design]['length']}


def write_bindings(ledger):
    lines = []
    for design, entry in sorted(ledger.items()):
        # An entry from another project (the MM9 spellbooks, level_generation/ui/mm9_spellbooks_20261108) names its
        # icons and title itself; the designs of this project bind each item's own icon.
        icons = entry.get('icons') or [f'mm9_item_{item}' for item in entry['items']]
        title = entry.get('title') or DESIGNS[design]['title']
        for icon in icons:
            lines.append(f"  - {{icon: {icon}, model: {entry['model']}, length: {entry['length']}}}   # {title}\n")
    os.makedirs(os.path.dirname(BINDINGS), exist_ok=True)
    with open(BINDINGS, 'w') as handle:
        handle.write(HEADER + ''.join(lines))
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'item_model_shapes.py'), '--bindings', BINDINGS],
                   check=True, cwd=REPO)
    print(len(lines), 'bindings for', len(ledger), 'models in', os.path.relpath(BINDINGS, REPO))


def main():
    ledger_path = os.path.join(HERE, 'ledger.json')
    ledger = json.load(open(ledger_path)) if os.path.exists(ledger_path) else {}
    designs = [] if sys.argv[1:] == ['--bindings'] else sys.argv[1:]
    for design in designs:
        install(design, ledger)
        with open(ledger_path, 'w') as handle:
            json.dump(ledger, handle, indent=1, sort_keys=True)
            handle.write('\n')
    write_bindings(ledger)


if __name__ == '__main__':
    main()
