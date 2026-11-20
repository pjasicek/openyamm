"""Fringe cards that the original rig left rigid on a fang or the abdomen: the largest gap (over Walking, Running,
Attack and Death) between each card's posed vertices and the nearest leg surface, against its rest gap.
Usage: blender -b -P card_gap.py (work/source.blend, work/face_piece.npy)"""
import os, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
sc = bpy.context.scene; body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
info = np.load(os.path.join(HERE, 'work', 'faces_info.npz')); d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz'))
f = d['faces']; pc = np.load(os.path.join(HERE, 'work', 'face_piece.npy'))  # make_groups.py pieces (python3: scipy)
sizes = np.bincount(pc); dom = info['dom'].astype(str)
legs = np.isin(pc, np.where(sizes > 800)[0]) & (sizes[pc] < 3000)
cards = {}
for p in np.unique(pc[(sizes[pc] < 150)]):
    sel = pc == p; top = max(set(dom[sel]), key=list(dom[sel]).count)
    if top.startswith('Fang') or top == 'Abdomen':
        cards[int(p)] = (top, np.unique(f[sel]))
legf = f[legs]
def gaps():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([v.co[:] for v in m.vertices]); ev.to_mesh_clear()
    t = BVHTree.FromPolygons([tuple(x) for x in P], [tuple(x) for x in legf])
    return {p: max(t.find_nearest(P[i])[3] for i in vs) for p, (_, vs) in cards.items()}
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
sc.frame_set(0); rest = gaps(); worst = {p: (0, '') for p in cards}
for act in ('Walking', 'Running', 'Attack', 'Death'):
    A = bpy.data.actions[act]; rig.animation_data.action = A
    for fr in range(int(A.frame_range[0]), int(A.frame_range[1]) + 1, 3):
        sc.frame_set(fr)
        for p, g in gaps().items():
            if g > worst[p][0]:
                worst[p] = (g, f'{act}:{fr}')
for p, (top, vs) in cards.items():
    print('CARD', p, top, len(vs), 'verts, rest gap', round(rest[p] * 100, 1), 'cm, worst', round(worst[p][0] * 100, 1), 'cm at', worst[p][1])
