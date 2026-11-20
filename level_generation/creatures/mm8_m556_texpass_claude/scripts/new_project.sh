#!/usr/bin/env bash
# Starts the next texture-pass project with this toolkit: claims <world>:<id>, creates <stem>_texpass_claude with the
# scripts, backs up the installed GLB and its actors.yml entries, adds the ledger row and prints the GLB's structure
# and texture_quality. Usage (repository root): new_project.sh <world> <stem> [owner texpass-texpass-2]
set -euo pipefail
cd "$(dirname "$0")/../../../.."
W=$1; S=$2; OWNER=${3:-texpass-texpass-2}
SRC="$(cd "$(dirname "$0")" && pwd)"
P=level_generation/creatures/${S}_texpass_claude
mkdir -p "$P"
TOKEN=$(python3 tools/creature_workspace.py claim --project "$P" --identity "$W:${S#${W}_}" --owner "$OWNER" --budget 20 \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")
mkdir -p "$P"/{work/before_texpass,scripts,textures,texturing,requests,review,export,references_hd}
cp "$SRC"/*.py "$SRC"/*.sh "$P/scripts/"
cp "assets_source/worlds/$W/models/$S.glb" "$P/work/before_texpass/"
echo "token $TOKEN identity $W:${S#${W}_}" > "$P/work/LEASE.txt"
echo "| $S | in progress (texpass-2) | texpass-2 | | | | | |" >> level_generation/creatures/audit_mm678_20261111/fixes/LEDGER_texpass.md
python3 - "$W" "$S" "$P" <<'EOF'
import sys, yaml
w, s, p = sys.argv[1:4]
d = yaml.safe_load(open(f'assets_dev/worlds/{w}/models/actors.yml'))['actors']
sel = [e for e in d if f'{s}.glb' in str(e.get('model', ''))]
yaml.safe_dump(sel, open(f'{p}/work/before_texpass/actors_entries.yml', 'w'), sort_keys=False)
print('descriptors', [e['descriptor'] for e in sel])
sys.path.insert(0, f'{p}/scripts')
from glb import Glb
g = Glb(f'{p}/work/before_texpass/{s}.glb'); d = g.doc
for i, m in enumerate(d['meshes']):
    for pr in m['primitives']:
        print(i, m['name'], 'mat', pr.get('material'), 'v', d['accessors'][pr['attributes']['POSITION']]['count'],
              't', d['accessors'][pr['indices']]['count'] // 3, m.get('extras') or '', 'variants' if pr.get('extensions') else '')
for i, m in enumerate(d['materials']):
    print('mat', i, m['name'], m.get('alphaMode', ''), [k for k in m if 'Texture' in k],
          m['pbrMetallicRoughness'].get('baseColorTexture'), 'ramps', len(m.get('extras', {}).get('openyamm_region_ramps', [])))
for i, im in enumerate(d['images']):
    print('img', i, im.get('name'), g.image(i).size)
print('variants', [v['name'] for v in d.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])])
print('clips', [a['name'] for a in d['animations']])
print('joints', [d['nodes'][j]['name'] for j in d['skins'][0]['joints']])
EOF
python3 level_generation/creatures/claude_shared/texture_quality.py "$P/work/before_texpass/$S.glb" --by-bone \
    --json "$P/work/quality_before.json" | grep -v '^    '
sha256sum "assets_source/worlds/$W/models/$S.glb" | cut -c1-16
echo "TOKEN $TOKEN"
