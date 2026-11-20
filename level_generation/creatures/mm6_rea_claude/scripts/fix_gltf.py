#!/usr/bin/env python3
"""Finalise the exported Reactor GLB: material contract and STEP toggles. Usage: fix_gltf.py in.glb out.glb

- Reactor_Glow: KHR_materials_unlit (screens, glowing liquid, arcs, lamps, glows), no edge darkening.
- Reactor_Metal: unlit as well, its texture carries baked light: the native frames are fullbright ("Lit") and the
  Hive's room light is dim, so lit metal read dull and dark next to the sprite (review/ingame_v2).
- Reactor_Flash: unlit and blended (alpha 0.7), single-sided.
- Reactor_Glass: blended, single-sided and unlit (painted highlights), no edge darkening.
- Reactor_Halo: unlit, blended soft blue glow tubes around the arcs.
- Reactor_Metal / Reactor_Glow: double-sided (identical culling in one mesh for tools/build_actor_lods.py).
- Scale channels of pure on/off parts become STEP, so a part appears and disappears between frames."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as R  # noqa: E402

CONTINUOUS = {'GooStream', 'GooBlob', 'Nozzle', 'CapGlow', 'BowlGlow'} | {f'Shard{k}' for k in range(1, 9)} | \
    {f'Debris{k}' for k in range(1, 9)} | {f'{p}{s}_Up' for p in ('LArm', 'UArm') for s in ('L', 'R')}
STEP = {f'Arc{k}' for k in range(1, 5)} | {f'ArcBig{k}' for k in range(1, 4)} | \
    {'Liq100', 'Liq60', 'Liq25', 'Glass', 'GlassBroken', 'Flash', 'DomeTop', 'Spire',
     'Crown', 'BowlLower', 'BowlTorn', 'LampRed', 'LampG1', 'LampG2'}

doc, binary = R.read_glb(Path(sys.argv[1]))
mats = {m['name']: m for m in doc['materials']}
assert set(mats) == {'Reactor_Metal', 'Reactor_Glow', 'Reactor_Glass', 'Reactor_Flash', 'Reactor_Halo'}, sorted(mats)
for name in ('Reactor_Glow', 'Reactor_Flash', 'Reactor_Metal', 'Reactor_Halo'):
    m = mats[name]
    m.setdefault('extensions', {})['KHR_materials_unlit'] = {}
    m.pop('normalTexture', None); m.pop('emissiveTexture', None); m.pop('emissiveFactor', None)
    pbr = m.setdefault('pbrMetallicRoughness', {})
    pbr.pop('metallicRoughnessTexture', None)
    pbr['metallicFactor'] = 0.0; pbr['roughnessFactor'] = 1.0
    m.setdefault('extras', {}).update(openyamm_edge_darkening=0.0, openyamm_specular=0.0)
mats['Reactor_Glow']['doubleSided'] = True
mats['Reactor_Glow'].pop('alphaMode', None)
flash = mats['Reactor_Flash']
flash['alphaMode'] = 'BLEND'; flash['doubleSided'] = False
flash['pbrMetallicRoughness']['baseColorFactor'] = [1.0, 1.0, 1.0, 0.7]
halo = mats['Reactor_Halo']                 # soft blue glow around the arcs
halo['alphaMode'] = 'BLEND'; halo['doubleSided'] = False
halo['pbrMetallicRoughness']['baseColorFactor'] = [0.55, 0.7, 1.0, 0.32]
glass = mats['Reactor_Glass']
glass['alphaMode'] = 'BLEND'; glass['doubleSided'] = False
glass['pbrMetallicRoughness'].update(metallicFactor=0.0, roughnessFactor=1.0)
# Unlit like the rest: its painted highlights are the reflection (the dim room muted lit glass to nothing).
glass.setdefault('extensions', {})['KHR_materials_unlit'] = {}
glass.setdefault('extras', {}).update(openyamm_edge_darkening=0.0)
metal = mats['Reactor_Metal']
metal['doubleSided'] = True
metal.pop('alphaMode', None)
used = set(doc.get('extensionsUsed', [])) | {'KHR_materials_unlit'}
doc['extensionsUsed'] = sorted(used)

names = [n.get('name') for n in doc['nodes']]
WAVES = {f'{p}Wave{k}' for p in ('Band', 'Lid') for k in range(1, 4)}   # switched by depth (translation)
stepped = 0
for anim in doc.get('animations', []):
    for ch in anim['channels']:
        node = names[ch['target']['node']]
        if (ch['target']['path'] == 'scale' and node in STEP) or (ch['target']['path'] == 'translation'
                                                                  and node in WAVES):
            anim['samplers'][ch['sampler']]['interpolation'] = 'STEP'
            stepped += 1
missing = (STEP | CONTINUOUS | WAVES) - set(names)
if missing:
    raise SystemExit(f'missing toggle nodes: {sorted(missing)}')
R.write_glb(Path(sys.argv[2]), doc, binary)
print('FIXED materials', sorted(mats), 'step channels', stepped, 'clips', [a['name'] for a in doc['animations']])
