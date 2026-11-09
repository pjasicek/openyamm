"""Locate signed-distance candidates so local open finger surfaces cannot masquerade as torso penetration."""
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import cfg
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=str(Path(args[0]) if args else P / 'work/lancer_complete.blend'))
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
rig.animation_data_create()
me = body.data
rest = np.array([v.co[:] for v in me.vertices])
pv = np.array([v.value for v in me.attributes['piece'].data])
gv = np.array([v.value for v in me.attributes['garment'].data])
groups = [g.name for g in body.vertex_groups]
dom = [groups[max(v.groups, key=lambda e: e.weight).group] for v in me.vertices]
W = np.zeros((len(rest), len(groups)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
hand = {s: cfg.hand_mask(rest, pv, s, np.array(rig.data.bones[f'B_{s}_Hand'].head_local),
        np.array(rig.data.bones[f'B_{s}_Forearm'].head_local), 0) for s in 'LR'}
for side in 'LR':
    ids = [i for i, n in enumerate(groups) if n.startswith(f'B_{side}_') and any(t in n for t in ('Hand', 'Finger'))]
    hand[side] |= W[:, ids].sum(1) > .25
samples = [(args[1],float(args[2]),args[3])] if args else [('Carbine_Attack',17,'R'),('Carbine_Fidget',22.5,'R'),('Carbine_Death',13,'L')]
for clip, frame, side in samples:
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(frame), subframe=frame-int(frame))
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    posed = np.array([v.co[:] for v in mesh.vertices])
    ev.to_mesh_clear()
    ids = [i for i, n in enumerate(groups) if n.startswith(f'B_{side}_') and
           any(t in n for t in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger'))]
    arm = W[:, ids].sum(1) > .2
    faces = [tuple(f.vertices) for f in me.polygons if all(gv[i] in (0, 3, 16) and
             not hand['L'][i] and not hand['R'][i] and not arm[i] for i in f.vertices)]
    tree = BVHTree.FromPolygons(posed.tolist(), faces)
    candidates = []
    for i in np.where(hand[side])[0]:
        loc, normal, face, distance = tree.find_nearest(Vector(posed[i]), .08)
        if loc is not None and (Vector(posed[i])-loc).dot(normal) < -.7*distance:
            candidates.append((distance, i, face))
    for distance, i, face in sorted(candidates, reverse=True)[:3]:
        print('HAND_CANDIDATE', clip, frame, side, round(distance, 4), int(i), dom[i], rest[i].tolist(),
              'nearest', [(dom[j], rest[j].tolist(), int(pv[j])) for j in faces[face]], flush=True)
