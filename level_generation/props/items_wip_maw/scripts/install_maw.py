"""Install the baked MAW crafting item models and bind them by icon.

python3 install_maw.py [design ...]   (from anywhere; not with -I: install_model.py imports its siblings)

Per design: the winding check (0 inverted closed parts), tools/install_model.py --world-items --name item_<icon>.glb,
then the design's binding in the MAW block at the end of assets_dev/engine/world_items/items.yml (written in
designs.json order, replacing the block), and tools/item_model_shapes.py for the bounds. Receipts: work/install.json."""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
BINDINGS = os.path.join(REPO, 'assets_dev', 'engine', 'world_items', 'items.yml')
WINDING = os.path.join(REPO, 'level_generation', 'decorations', 'mm8_3d', 'animated', 'scripts', 'check_winding.py')
MARKER = '  # MAW ruleset crafting items (level_generation/props/items_wip_maw):'


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def install(name, receipts):
    icon = DESIGNS[name]['icon']
    export = os.path.join(HERE, 'work', 'codex_tex', f'{name}_export.glb')
    winding = subprocess.run([sys.executable, WINDING, export], capture_output=True, text=True)
    print(winding.stdout.strip().splitlines()[-1] if winding.stdout.strip() else winding.stderr.strip())
    if winding.returncode != 0:
        raise SystemExit(f'{name}: winding check failed')
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'install_model.py'), export, '--world-items',
                    '--name', f'item_{icon}.glb'], check=True, cwd=REPO)
    receipts[name] = {'icon': icon, 'export_sha256': sha(export),
                      'source': f'assets_source/engine/world_items/models/item_{icon}.glb',
                      'source_sha256': sha(os.path.join(REPO, 'assets_source', 'engine', 'world_items', 'models',
                                                        f'item_{icon}.glb'))}


def bind():
    text = open(BINDINGS).read()
    if MARKER in text:
        text = text[:text.index(MARKER)]
    lines = [MARKER]
    for name, entry in DESIGNS.items():
        icon = entry['icon']
        model = f'engine/world_items/models/item_{icon}.glb'
        if os.path.exists(os.path.join(REPO, 'assets_dev', model)):
            lines.append(f"  - {{icon: {icon}, model: {model}, length: {entry['length']}}}   # {entry['title']}")
    with open(BINDINGS, 'w') as handle:
        handle.write(text.rstrip('\n') + '\n' + '\n'.join(lines) + '\n')
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'item_model_shapes.py')], check=True, cwd=REPO)


def main():
    names = sys.argv[1:] or [n for n in DESIGNS
                             if os.path.exists(os.path.join(HERE, 'work', 'codex_tex', f'{n}_export.glb'))]
    path = os.path.join(HERE, 'work', 'install.json')
    receipts = json.load(open(path)) if os.path.exists(path) else {}
    for name in names:
        install(name, receipts)
        with open(path, 'w') as handle:
            json.dump(receipts, handle, indent=1)
    bind()


main()
