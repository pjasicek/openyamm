"""Bow-carry fix on every clip but Attack (2026-10-19 user review of the bow wrist: "ok fix the wrist first"): per
frame the bow keeps its exact pose and the left arm is re-solved for a straight wrist (carry.hold). Rebakes LArm,
LForeArm, LHand and Bow; loop clips keep their exact join and Dead stays Death's last frame. Attack comes from
animate_attack_v2.py, which starts and ends in the same hold.
Usage: blender -b -P carry_fix.py -- <in.blend> <out.blend> [clip,clip...]"""
from pathlib import Path
import bpy, sys, json, os
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'mm6_rat_claude/scripts')); import posing as Q
sys.path.insert(0, str(Path(__file__).resolve().parent)); import carry
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; pb = rig.pose.bones
G = json.loads((P / 'work/equipment.json').read_text())
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
CLIPS = args[2].split(',') if len(args) > 2 else ['Standing', 'Walking', 'Running', 'Fidget', 'Hit', 'Cast', 'Death', 'Dead']
LOOPS = {'Standing', 'Walking', 'Running', 'Fidget'}
BONES = ('LArm', 'LForeArm', 'LHand', 'Bow')
report = {}


def bake(f):
    for n in BONES:
        b = pb[n]
        for path in ('location', 'rotation_quaternion', 'scale'):
            b.keyframe_insert(path, frame=f, group=n)


def local(n):
    b = pb[n]; return b.location.copy(), b.rotation_quaternion.copy(), b.scale.copy()


def set_local(n, v):
    b = pb[n]; b.location, b.rotation_quaternion, b.scale = v


held = None
for name in CLIPS:
    act = bpy.data.actions[name]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); frames = range(f0, f1 + 1)
    if name == 'Dead' and held is not None:
        for f in frames:
            sc.frame_set(f)
            for n in BONES:
                set_local(n, held[n])
            bpy.context.view_layer.update(); bake(f)
        report[name] = {'frames': len(frames), 'held': 'Death last frame'}; print('CARRY', name, report[name]); continue
    free = {'floor': .01} if name == 'Death' else None
    cands = []
    for f in frames:                                              # candidates per frame, then the cheapest path
        sc.frame_set(f); cands.append(carry.candidates(rig, rest, G, pb['Bow'].matrix.copy(), free))
    chosen = carry.path(cands, pin_end=name in ('Hit', 'Cast'))       # both end in the Standing pose
    if os.environ.get('CARRY_DEBUG') == name:
        for f, c, h in zip(frames, cands, chosen):
            print('DBG', f, 'best', round(c[0]['cost'], 1), round(c[0]['bend'], 1), c[0]['bow'], [round(x, 2) for x in c[0]['E']],
                  'chosen', round(h['cost'], 1), round(h['bend'], 1), h['bow'], [round(x, 2) for x in h['E']])
    roll = {'LArm': 0, 'LForeArm': 0}; last = {}; first = None
    for f, h in zip(frames, chosen):
        sc.frame_set(f)
        if name in LOOPS and f == f1:
            for n in BONES:
                set_local(n, first[n])
            bpy.context.view_layer.update()
        else:
            if name in ('Hit', 'Cast') and f == f1:                   # the Standing pose: settle as Standing's first
                roll = {'LArm': 0, 'LForeArm': 0}
            carry.apply(rig, Q, rest, h, roll)
        for n in BONES:
            q = pb[n].rotation_quaternion
            if n in last and q.dot(last[n]) < 0:
                pb[n].rotation_quaternion = -q
            last[n] = pb[n].rotation_quaternion.copy()
        if f == f0:
            first = {n: local(n) for n in BONES}
        bake(f)
    if name == 'Death':
        held = {n: local(n) for n in BONES}
    report[name] = {'frames': len(frames), 'solver_bend_max': round(max(h['bend'] for h in chosen), 1),
                    'bow_change_max': [max(abs(h['bow'][0]) for h in chosen), max(abs(h['bow'][1]) for h in chosen),
                                       max(h['bow'][2] for h in chosen)]}
    print('CARRY', name, report[name])
rig.animation_data.action = bpy.data.actions['Standing']; rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=args[1])
print('CARRY_FIX', json.dumps(report))
