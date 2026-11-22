"""Installs reviewed Xeen ground-item models and writes the Xeen world's own bindings (MM9's install_mm9.py, adapted).

Per design: the winding check (0 inverted closed parts), then tools/install_model.py --world-items --world xeen (source
assets_source/worlds/xeen/world_items/models/item_xeen_<suffix>.glb, cooked runtime copy in assets_dev) and its line in
ledger.json. Then assets_dev/worlds/xeen/world_items/items.yml is rewritten from the ledger plus the reuse designs of
classification.json (an installed engine model, its engine binding's length): one binding per xeen_item_* icon, and
tools/item_model_shapes.py fills the bounds. Route meshy designs (lane S's statuettes and dolls) install the same way.
Usage: python3 scripts/install_xeen.py <design> [...]    (without -I: the installer and cook import sibling modules)
       python3 scripts/install_xeen.py --bindings        (rewrite the bindings from the ledger only)"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
CLASSIFICATION = json.load(open(os.path.join(HERE, 'classification.json')))
WINDING = os.path.join(REPO, 'level_generation', 'decorations', 'mm8_3d', 'animated', 'scripts', 'check_winding.py')
BINDINGS = os.path.join(REPO, 'assets_dev', 'worlds', 'xeen', 'world_items', 'items.yml')
ENGINE_BINDINGS = os.path.join(REPO, 'assets_dev', 'engine', 'world_items', 'items.yml')
MODELS = 'worlds/xeen/world_items/models'
HEADER = """# The Xeen world's own items lying on the ground in 3D, by inventory icon (items.txt "Pic File"), added to the
# engine's engine/world_items/items.yml (GameDataLoader; an icon bound in both fails). Only the xeen_item_* icons;
# two of them reuse an engine model. Written by level_generation/props/items_xeen_claude/scripts/install_xeen.py;
# bounds by tools/item_model_shapes.py. length: world units of the model's longest horizontal side; see
# devdocs/GROUND_ITEMS_3D_PLAN.md.
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
    name = f"item_xeen_{design[1:]}.glb"
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'install_model.py'), export, '--world-items',
                    '--world', 'xeen', '--name', name], check=True, cwd=REPO)
    ledger[design] = {'route': DESIGNS[design]['route'], 'builder': DESIGNS[design]['builder'],
                      'export': os.path.relpath(export, REPO), 'sha256': sha256(export),
                      'model': f'{MODELS}/{name}', 'icon': DESIGNS[design]['icon'],
                      'items': DESIGNS[design]['items'], 'length': DESIGNS[design]['length']}


def engine_binding(icon):
    for line in open(ENGINE_BINDINGS):
        match = re.search(r'\{icon: (\S+), model: (\S+), length: ([\d.]+)', line)
        if match and match.group(1) == icon:
            return match.group(2), float(match.group(3))
    raise SystemExit(f'engine icon {icon} is not bound')


def write_bindings(ledger):
    for design, entry in CLASSIFICATION.items():
        if entry['route'] == 'reuse':
            model, length = engine_binding(entry['builder'])
            ledger[design] = {'route': 'reuse', 'engine_icon': entry['builder'], 'model': model,
                              'icon': entry['icon'], 'items': entry['items'], 'length': length}
    lines = []
    for design, entry in sorted(ledger.items()):
        title = CLASSIFICATION[design]['name']
        lines.append(f"  - {{icon: {entry['icon']}, model: {entry['model']}, length: {entry['length']}}}   # {title}\n")
    os.makedirs(os.path.dirname(BINDINGS), exist_ok=True)
    with open(BINDINGS, 'w') as handle:
        handle.write(HEADER + ''.join(lines))
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'item_model_shapes.py'), '--bindings', BINDINGS],
                   check=True, cwd=REPO)
    print(len(lines), 'bindings in', os.path.relpath(BINDINGS, REPO))


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
    with open(ledger_path, 'w') as handle:
        json.dump(ledger, handle, indent=1, sort_keys=True)
        handle.write('\n')


if __name__ == '__main__':
    main()
