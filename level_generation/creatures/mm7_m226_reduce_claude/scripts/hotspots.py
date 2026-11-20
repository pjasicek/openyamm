"""Where a candidate's error sits: every 3rd frame of every clip, each source vertex's distance to the candidate;
source vertices over REA_HOT_MM (default 5) in any frame, clustered by rest position (3 cm grid), with the dominant
bone, region and worst clip. Writes work/hot_<cand>.npy (per source vertex: max distance in mm).
Usage: blender -b -P hotspots.py -- <Cand_NN>"""
import os, sys, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cn = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; cand = bpy.data.objects[cn]
TH = float(os.environ.get('REA_HOT_MM', '5')) / 1000
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); rest = d['verts']
reg = np.load(os.path.join(HERE, 'work', 'regions.npy')); vreg = np.zeros(len(rest), int); vreg[d['faces'].ravel()] = np.repeat(reg, 3)
names = {g.index: g.name for g in src.vertex_groups}
dom = [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in src.data.vertices]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
worst = np.zeros(len(rest)); where = [''] * len(rest)
for act in bpy.data.actions:
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    for fr in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 3):
        sc.frame_set(fr); bs = ev(src); bc = ev(cand); tc = BVHTree.FromBMesh(bc)
        for v in bs.verts:
            e = tc.find_nearest(v.co)[3]
            if e > worst[v.index]:
                worst[v.index] = e; where[v.index] = f'{act.name}:{fr}'
        bs.free(); bc.free()
np.save(os.path.join(HERE, 'work', f'hot_{cn}.npy'), worst * 1000)
hot = np.flatnonzero(worst > TH); cells = {}
for i in hot:
    cells.setdefault(tuple(np.floor(rest[i] / .03).astype(int)), []).append(i)
print('HOT', cn, len(hot), 'source vertices over', TH * 1000, 'mm')
for k, vs in sorted(cells.items(), key=lambda kv: -len(kv[1]))[:25]:
    i = max(vs, key=lambda j: worst[j])
    print(f'  n {len(vs):3d} max {worst[i]*1000:5.1f}mm at {np.round(rest[vs].mean(0), 3)} region {vreg[i]} {dom[i]} {where[i]}')
