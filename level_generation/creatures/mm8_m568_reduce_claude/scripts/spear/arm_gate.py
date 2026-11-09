"""Arm and hand gate (humanoid playbook) for a spear blend, every second 48 Hz frame of every clip:
- polearm into the body: weapon vertices inside the body surface (signed distance to the nearest face), outside the
  two grip zones (12 cm around each hand contact on the shaft); Death/Dead after the release is included;
- hands into the torso: hand and finger vertices inside the surface of the non-arm body faces;
- wrist swing: change of the hand-forearm angle from rest (budget 60 degrees), forearm twist of the twist bone
  relative to the forearm (budget ~90 degrees, continuity: largest frame-to-frame jump).
Usage: blender -b -P arm_gate.py -- <tag> [S_R S_L] -> work/arm_gate_<tag>.json"""
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
P = Path(__file__).resolve().parents[2]; args = sys.argv[sys.argv.index('--') + 1:]; tag = args[0]
audit = json.loads((P / f'work/spear_{tag}_audit.json').read_text()); S = {'R': audit['S_R'], 'L': audit['S_L']}
bpy.ops.wm.open_mainfile(filepath=str(P / f'work/spear_{tag}.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; weapon = bpy.data.objects['PolearmMesh']
names = {g.index: g.name for g in body.vertex_groups}
def wsum(v, pred): return sum(g.weight for g in v.groups if pred(names[g.group]))
armish = lambda n: any(k in n for k in ('Arm', 'Forearm', 'Hand', 'Finger', 'Clavicle'))
handish = lambda n: 'Hand' in n or 'Finger' in n
me = body.data
hand_v = np.array([wsum(v, handish) > .5 for v in me.vertices]); arm_v = np.array([wsum(v, armish) > .2 for v in me.vertices])
torso_faces = [list(p.vertices) for p in me.polygons if not arm_v[list(p.vertices)].any()]
def hand_dirs(get):
    # anatomical directions: forearm = elbow -> wrist, hand = wrist -> middle finger base
    e, w, k = get('B_{}_Forearm'), get('B_{}_Hand'), get('B_{}_Finger2')
    return (k - w).normalized(), (w - e).normalized()
rest_ang = {sd: (lambda h, f: h.angle(f))(*hand_dirs(lambda n: rig.data.bones[n.format(sd)].head_local)) for sd in 'LR'}
DIRS = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((-1, 0, 0))]
def inside(tree, p):
    """Ray parity in four directions; inside only when three or more agree (the body has small open seams)."""
    votes = 0
    for d in DIRS:
        hits, o = 0, Vector(p)
        for _ in range(40):
            loc, nrm, idx, dist = tree.ray_cast(o, d)
            if loc is None:
                break
            hits += 1; o = loc + d * 1e-4
        votes += hits % 2
    return votes >= 3
def signed(tree, polys_n, co, pts):
    out = []
    for p in pts:
        loc, nrm, idx, dist = tree.find_nearest(Vector(p))
        out.append(-dist if (Vector(p) - loc).dot(nrm) < 0 and dist > .002 and inside(tree, p) else dist)
    return np.array(out)
report = {}
for act in bpy.data.actions:
    clip = act.name; rig.animation_data.action = act; n = int(act.frame_range[1]); worst = {'weapon_mm': 0, 'weapon_at': None, 'hand_mm': 0, 'hand_at': None, 'wrist_swing_deg': 0, 'twist_deg': 0, 'twist_jump_deg': 0, 'twist_jump_at': None}
    prev = {}
    for f in range(1, n + 1, 2):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        eb = body.evaluated_get(dg).to_mesh(); bco = np.array([v.co[:] for v in eb.vertices]); body.evaluated_get(dg).to_mesh_clear()
        bm = bmesh.new(); bm.from_object(body, dg); tree = BVHTree.FromBMesh(bm); bm.free()
        ttree = BVHTree.FromPolygons([Vector(c) for c in bco], torso_faces, all_triangles=False)
        ew = weapon.evaluated_get(dg).to_mesh(); wco = np.array([weapon.matrix_world @ v.co for v in ew.vertices]); weapon.evaluated_get(dg).to_mesh_clear()
        pb = rig.pose.bones['Polearm']; delta = rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()
        o = np.array(delta.translation); ax = np.array(delta.to_3x3() @ Vector((0, 0, 1)))  # the mesh's shaft is local z
        s = (wco - o) @ ax
        free = clip in ('Death', 'Dead') and f > 0.24 * 48 + 1
        zone = np.zeros(len(wco), bool)
        if not (clip == 'Dead' or (clip == 'Death' and f > .6 * 48)):
            for sd in 'LR':
                zone |= np.abs(s - S[sd]) < .12
        d = signed(tree, None, None, wco[~zone]) if (~zone).any() else np.zeros(1)
        if -d.min() * 1000 > worst['weapon_mm']:
            worst['weapon_mm'] = float(-d.min() * 1000); worst['weapon_at'] = f - 1
            sel = wco[~zone][int(np.argmin(d))]; worst['weapon_pt'] = [round(float(x), 3) for x in sel]; worst['weapon_s'] = round(float((sel - o) @ ax), 3)
        hd = signed(ttree, None, None, bco[hand_v])
        if -hd.min() * 1000 > worst['hand_mm']:
            worst['hand_mm'] = float(-hd.min() * 1000); worst['hand_at'] = f - 1
            worst['hand_pt'] = [round(float(x), 3) for x in bco[hand_v][int(np.argmin(hd))]]
            worst['hand_side'] = 'L' if bco[hand_v][int(np.argmin(hd))][0] > 0 else 'R'
        for sd in 'LR':
            H = rig.pose.bones[f'B_{sd}_Hand'].matrix.to_3x3(); F = rig.pose.bones[f'B_{sd}_Forearm'].matrix.to_3x3(); T = rig.pose.bones[f'B_{sd}_ForearmTwist'].matrix.to_3x3()
            h_, f_ = hand_dirs(lambda n: rig.pose.bones[n.format(sd)].head)
            swing = abs(math.degrees(h_.angle(f_) - rest_ang[sd])); (worst.__setitem__('wrist_swing_deg', swing), worst.__setitem__('wrist_at', f'{sd} {f - 1}')) if swing > worst['wrist_swing_deg'] else None
            q = (F.inverted() @ H).to_quaternion(); tw = math.degrees(2 * math.atan2(q.y, q.w)); tw = (tw + 180) % 360 - 180
            worst['twist_deg'] = max(worst['twist_deg'], abs(tw))
            if sd in prev and abs(tw - prev[sd]) > worst['twist_jump_deg']:
                worst['twist_jump_deg'] = abs(tw - prev[sd]); worst['twist_jump_at'] = f'{sd} {f - 1}'
            prev[sd] = tw
    report[clip] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in worst.items()}
    print('GATE', clip, report[clip], flush=True)
(P / f'work/arm_gate_{tag}.json').write_text(json.dumps(report, indent=1) + '\n')
