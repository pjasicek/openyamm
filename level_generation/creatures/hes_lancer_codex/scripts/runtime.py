"""Build project-owned runtime files through the shared Kreegan/LOD pipeline. Never installs assets."""
import json
import shutil
import os
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parents[1]
R = P.parents[2]
W, E, S = P / 'work', P / 'export', P / 'scripts'
SHARED = P.parent / 'claude_shared'
NAMES = tuple(sys.argv[2:]) or ('hes_lancer', 'hes_lancer_twin')
assert set(NAMES) <= {'hes_lancer','hes_lancer_twin','hes_forgemaster'}

def run(script, *args, env=None):
    print('RUNTIME', Path(script).name, *map(str, args), flush=True)
    subprocess.run(['python3', str(script), *map(str, args)], check=True,
                   env={**os.environ, **(env or {})})

phase = sys.argv[1]
if phase == 'prepare':
    for name in NAMES:
        run(R / 'tools/prepare_actor_glb.py', E / f'{name}_lod0.glb', W / f'{name}_runtime_lod0.glb')
elif phase == 'variants':
    for name in NAMES:
        run(SHARED / 'region_variants.py', W / f'{name}_lods.glb', W / f'{name}_variants.glb',
            P / ('textures/forge_ramps.json' if name == 'hes_forgemaster' else 'textures/lancer_ramps.json'), '--extra', 'Lancer_Body', 'openyamm_specular=0',
            '--extra', 'Lancer_Body', 'pbr.metallicFactor=0',
            '--extra', 'Lancer_Plate', 'openyamm_specular=0.5', '--extra', 'Lancer_Plate', 'openyamm_specular_mask=true',
            '--extra', 'Lancer_Plate_C', 'pbr.metallicFactor=0.85')
        run(S / 'glow_variants.py', W / f'{name}_variants.glb', W / f'{name}_glow.glb')
        prefixes = ['Lancer_Plate', 'HKR_Glow', 'Lancer_Resin', 'Lancer_Ancient', 'Forge_Brass']
        if name == 'hes_forgemaster':
            items = [{'name': 'hes_thunder_maul', 'joint': 'Thunder_Maul', 'materials': prefixes}]
        else:
            items = [{'name': 'hes_ion_lance_twin' if name.endswith('twin') else 'hes_ion_lance',
                      'joint': 'Rifle', 'materials': prefixes},
                     {'name': 'hes_lancer_graft', 'joint': 'Ancient_Graft', 'materials': prefixes,
                      'lod_from': [0, 0, 0, 0]}]
        config = S / f'attachments_{name}.json'
        config.write_text(json.dumps(items, indent=2) + '\n')
        run(S / 'split_attachments_hkr.py', W / f'{name}_glow.glb', '--body', W / f'{name}_split.glb',
            '--items', config, '--outdir', E)
        (E / 'attachments.json').rename(P / f'review/attachments_{name}.json')
        if name.endswith('twin'):
            continue
        run(S / 'rebuild_shadows_hkr.py', W / f'{name}_split.glb', W / f'{name}_shadows.glb')
        run(S / 'shrink_shadow_lods.py', W / f'{name}_shadows.glb', W / f'{name}_near.glb', env={'MESH': 'Lancer'})
elif phase == 'far':
    for name in [n for n in NAMES if not n.endswith('twin')]:
        run(P / 'lodrep/repair_glb.py', W / f'{name}_near.glb', W / f'lodrep_{name}', W / f'{name}_far.glb',
            env={'LOD_REPAIR_PYTHON': '/tmp/lancer_lod_venv/bin/python'})
        result = json.loads((W / f'lodrep_{name}/result.json').read_text())
        assert result['passed'], result
elif phase == 'finish':
    for name, weapon, joint, family in [('hes_lancer', 'hes_ion_lance_twin', 'Rifle', 'Carbine'),
                                       ('hes_forgemaster', 'hes_thunder_maul', 'Thunder_Maul', 'Forge')]:
        if name not in NAMES:
            continue
        if family == 'Forge':
            run(S / 'forge_floor.py', W / f'{name}_far.glb', E / f'{name}.glb',
                P / 'review/forge_floor_runtime.json')
        else:
            run(S / 'death_carbine_floor.py', W / f'{name}_far.glb', E / f'{name}.glb', E / f'{weapon}.glb',
                env={'WEAPON': joint, 'DEATH': family + '_Death', 'DEAD': family + '_Dead'})
    for name in ('hes_lancer', 'hes_forgemaster', 'hes_ion_lance', 'hes_ion_lance_twin',
                 'hes_thunder_maul', 'hes_lancer_graft'):
        if name in ('hes_forgemaster','hes_thunder_maul') and 'hes_forgemaster' not in NAMES:
            continue
        if name not in ('hes_forgemaster','hes_thunder_maul') and 'hes_lancer' not in NAMES:
            continue
        target = E / f'{name}.glb'
        raw = target.read_bytes()
        import struct
        document = json.loads(raw[20:20+struct.unpack_from('<I', raw, 12)[0]])
        if any(m.get('name', '').startswith('HKR_Glow') for m in document['materials']):
            run(SHARED / 'emission.py', target, target, '--material', 'HKR_Glow',
                '--color', 'lancer_a=1.0,0.42,0.08', '--color', 'lancer_b=1.0,0.36,0.06',
                '--color', 'lancer_c=1.0,0.86,0.55', '--color', 'forgemaster=1.0,0.20,0.015', '--strength', '1.0')
    for name in [n for n in NAMES if not n.endswith('twin')]:
        run(S / 'check_key_times.py', E / f'{name}.glb')
else:
    raise ValueError(phase)
