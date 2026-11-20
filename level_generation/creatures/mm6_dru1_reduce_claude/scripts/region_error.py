"""Per-region two-way surface error of ladder candidates (work/ladder.blend) over every 4th frame of every clip:
source vertex -> candidate surface, grouped by the source vertex's dominant-bone region (face, head, hands, cloak,
legs, torso). Usage: REA_CANDS=Cand_70,Cand_66 blender -b -P scripts/region_error.py"""
import os, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
names = {g.index: g.name for g in src.vertex_groups}
def lab(n):
    if n in ('B_Head', 'B_Neck'): return 'head'
    if any(k in n for k in ('Hand', 'Finger')): return 'hands'
    if n.startswith('Cloak'): return 'cloak'
    if any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe')): return 'legs'
    return 'torso'
reg = []
for v in src.data.vertices:
    gs = [g for g in v.groups if names[g.group] != 'ReduceProtect']
    reg.append(lab(names[max(gs, key=lambda g: g.weight).group]) if gs else 'torso')
reg = np.array(reg)
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
for cn in os.environ.get('REA_CANDS', 'Cand_70').split(','):
    errs = []
    for act in bpy.data.actions:
        rig.animation_data.action = act
        for f in range(0, int(act.frame_range[1]) + 1, 4):
            sc.frame_set(f); bs = ev(src); bc = ev(bpy.data.objects[cn]); tc = BVHTree.FromBMesh(bc)
            errs.append([tc.find_nearest(v.co)[3] for v in bs.verts]); bs.free(); bc.free()
    e = np.array(errs) * 1000
    print('REGION', cn, ' '.join(f"{r}:{int((reg == r).sum())}v p99 {np.percentile(e[:, reg == r], 99):.1f} max {e[:, reg == r].max():.1f}"
                                  for r in ['head', 'hands', 'cloak', 'legs', 'torso']), flush=True)
