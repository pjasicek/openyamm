"""Write gates.json for claude_shared/gates/run_gates.py from the weapon mounts (scripts/weapons.json, clips_lib.mount_matrix:
the attachments' node frames), the measured events (work/events.json) and the rig's hands (six claws: Finger0..5; the
palm axis from the knuckle line, as hes_overseer_codex/scripts/run_preview_gates.py). Each prop is checked only in
its own row's clips; a two-handed weapon's left hand at its support point. Run in Blender (mathutils). Args: none"""
import bpy, sys, os, json
from pathlib import Path
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_lib as cl
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'assembly_all.blend'))
rig = bpy.data.objects['Rig']
M = json.loads((P / 'scripts' / 'weapons.json').read_text()); EV = json.loads((P / 'work' / 'events.json').read_text())
PROPS = [  # weapon, attachment, prefix, kind, hands, weapon-coords edge (cutting side) or None
    ('noble_fang', 'hes_noble_fang', 'Noble', 'melee', ['R'], (-1, 0, 0)),
    ('noble_sidearm', 'hes_noble_sidearm', 'Noble', 'other', [], None),
    ('ssekh_fang_r', 'hes_ssekh_fang_r', 'Ssekh', 'melee', ['R'], (1, 0, 0)),
    ('ssekh_fang_l', 'hes_ssekh_fang_l', 'Ssekh', 'melee', ['L'], (1, 0, 0)),
    ('phase_cleaver', 'hes_mraal_cleaver', 'Mraal', 'melee', ['R', 'L'], (1, 0, 0)),
    ('storm_rifle', 'hes_xith_storm_rifle', 'Xith', 'other', ['R', 'L'], None),
    ('lancer_carbine', 'hes_gate_carbine', 'Gate', 'other', ['R', 'L'], None),
    ('bastion_emitter', 'hes_gate_emitter', 'Gate', 'shield', [], None),
    ('gorget_seal', 'hes_gate_gorget', 'Gate', 'other', [], None),
]
props = []
for w, att, pfx, kind, hands, edge in PROPS:
    m = M[w]; T = cl.mount_matrix(m)
    box = lambda c, r=0.03, h=0.06: {'bounds': [[c[0] - r, c[1] - r, c[2] - h], [c[0] + r, c[1] + r, c[2] + h]]}
    p = {'name': w, 'file': f'export/{att}.glb', 'node': m['socket'], 'kind': kind, 'clips': [f'{pfx}_*'],
         'grip_point': [0, 0, 0], 'grip_surface': box((0, 0, 0)), 'hands': []}
    for s in hands:
        if s == 'R' or (s == 'L' and 'support' not in m):
            p['hands'].append({'side': s})
        else:
            sp = list(T @ Vector(m['support']['point']))
            p['hands'].append({'side': 'L', 'grip_point': [round(x, 4) for x in sp], 'surface': box(sp)})
    if kind == 'melee':
        p['edge_axis'] = [round(x, 4) for x in (T.to_3x3() @ Vector(edge)).normalized()]
        p['impacts'] = {f'{pfx}_AttackMelee': EV[pfx]['attack_melee']['impact']}
    props.append(p)
hands = {}
for side in 'LR':
    hn = rig.data.bones[f'B_{side}_Hand'].matrix_local
    a = rig.data.bones[f'B_{side}_Finger1'].head_local - hn.translation
    b = rig.data.bones[f'B_{side}_Finger5'].head_local - hn.translation
    n = a.cross(b).normalized() * (1 if side == 'R' else -1)
    hands[side] = {'palm_axis': [round(x, 5) for x in (hn.to_3x3().inverted() @ n)],
                   'fingers': [f'B_{side}_Finger{i}' for i in range(6)]}
fly = {'pelvis_min_m': 0.5, 'pelvis_max_m': 1.2, 'trunk_lean_deg': 60}
config = {'version': 1,
          'clips': {'rest': ['Mraal_Standing'], 'walk': ['Mraal_Walking'], 'run': ['Mraal_Running'],
                    'attack': ['*_Attack*', '*_Cast', 'Ssekh_Dive', 'Mraal_Cleave', 'Xith_ChargedShot']},
          'props': props, 'hands': hands, 'cloth': [],
          'posture': {'*': fly, 'Mraal_*': {'pelvis_min_m': 0.4, 'pelvis_max_m': 1.0, 'trunk_lean_deg': 70},
                      '*_Death': {'pelvis_min_m': 0.0, 'pelvis_max_m': 1.2, 'trunk_lean_deg': 180},
                      '*_Dead': {'pelvis_min_m': 0.0, 'pelvis_max_m': 1.2, 'trunk_lean_deg': 180}},
          'clip_thresholds': {f'{p}_Hit': {'rotation_step_deg': 30} for p in ('Noble', 'Ssekh', 'Xith', 'Gate')},
          'refine_hz': 48}   # (the flying demon's native hit snaps its wings 27.7 deg in one 1/48 s step)
(P / 'gates.json').write_text(json.dumps(config, indent=1))
print('GATES_CONFIG', len(props), 'props'); sys.stdout.flush(); os._exit(0)
