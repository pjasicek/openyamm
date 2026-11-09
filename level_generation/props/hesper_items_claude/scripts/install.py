"""Installs reviewed Hesper item models into the stage: the winding check (0 inverted closed parts), then the
export's entry in level_generation/projects/hesper_stage/item_models.yml (stage.py copies, cooks and binds it, and
runs tools/item_model_shapes.py on the staged bindings) and its line in ledger.json. Never writes assets_dev.
Usage: python3 -I install.py <icon> [icon ...]"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
STAGE_MODELS = os.path.join(REPO, 'level_generation', 'projects', 'hesper_stage', 'item_models.yml')
WINDING = os.path.join(REPO, 'level_generation', 'decorations', 'mm8_3d', 'animated', 'scripts', 'check_winding.py')
HEADER = ("# Hesper items' own ground models (level_generation/props/hesper_items_claude, installed by its "
          "install.py); stage.py\n# cooks each as worlds/hesper/models/item_<icon>.glb and binds it in place of the "
          "stand-in of "
          "items.yml's `ground`.\n")


def main():
    designs = json.load(open(os.path.join(HERE, 'classification.json')))
    ledger_path = os.path.join(HERE, 'ledger.json')
    ledger = json.load(open(ledger_path)) if os.path.exists(ledger_path) else {}
    for icon in sys.argv[1:]:
        export = os.path.join(HERE, 'work', f'{icon}_export.glb')
        check = subprocess.run([sys.executable, WINDING, export], capture_output=True, text=True)
        print(check.stdout.strip())
        if check.returncode != 0:
            raise SystemExit(f'{icon}: winding check failed')
        with open(export, 'rb') as stream:
            digest = hashlib.sha256(stream.read()).hexdigest()
        bake = json.load(open(os.path.join(HERE, 'codex_tex', icon, 'bake.json')))
        ledger[icon] = {'route': designs[icon]['route'], 'export': os.path.relpath(export, REPO), 'sha256': digest,
                        'triangles': bake['triangles'], 'registration': bake['registration'],
                        'items': [item['id'] for item in designs[icon]['items']]}
    with open(ledger_path, 'w') as handle:
        json.dump(ledger, handle, indent=1, sort_keys=True)
        handle.write('\n')
    # ground_lengths.json: binding lengths corrected after the bake (the stage scales the model to them).
    lengths = json.load(open(os.path.join(HERE, 'ground_lengths.json')))['lengths']
    lines = []
    for icon, entry in sorted(ledger.items()):
        length = f", length: {lengths[icon]}" if icon in lengths else ''
        lines.append(f"  - {{icon: {icon}, source: {entry['export']}{length}}}\n")
    with open(STAGE_MODELS, 'w') as handle:
        handle.write(HEADER + 'models:\n' + ''.join(lines))
    print(len(ledger), 'models in', os.path.relpath(STAGE_MODELS, REPO))


main()
