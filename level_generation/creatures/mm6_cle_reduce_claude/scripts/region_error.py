"""Two-way surface error of each candidate in work/ladder.blend per source region (work/regions.npy) over a few
frames, to see which region drives p99. Usage: blender -b -P region_error.py [-- Clip:frame ...]"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
reg = np.load(os.path.join(HERE, 'work', 'regions.npy'))
NAMES = ['rest', 'face', 'hair', 'lhand', 'rhand', 'cloak', 'tie']
frames = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['Standing:0', 'Walking:6', 'Walking:18', 'Attack:20', 'Hit:8', 'Death:12']
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); b.faces.ensure_lookup_table(); return b
vreg = np.zeros(len(src.data.vertices), int)
for p in src.data.polygons:
    for v in p.vertices: vreg[v] = reg[p.index]
cands = sorted(o.name for o in bpy.data.objects if o.name.startswith('Cand_'))
acc = {c: {k: [] for k in range(7)} for c in cands}
for fr in frames:
    clip, f = fr.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    bs = ev(src); ts = BVHTree.FromBMesh(bs)
    for c in cands:
        bc = ev(bpy.data.objects[c]); tc = BVHTree.FromBMesh(bc)
        for v in bs.verts:
            acc[c][vreg[v.index]].append(tc.find_nearest(v.co)[3])
        for v in bc.verts:
            co, _, fi, dist = ts.find_nearest(v.co)
            acc[c][reg[fi]].append(dist)
for c in cands:
    print(c, '  '.join(f'{NAMES[k]} p99 {np.percentile(a, 99) * 1000:.1f} max {max(a) * 1000:.0f}' for k, a in acc[c].items() if a))
