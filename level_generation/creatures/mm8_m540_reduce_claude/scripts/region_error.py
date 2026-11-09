"""Rest-pose error by region: source vertex -> candidate surface distance, p99/max per dominant bone family and per
head/body texture set (head = u > 0.5). Usage: blender -b -P region_error.py [-- <frame spec Clip:frame>]"""
import os, sys, bpy, bmesh, numpy as np, collections
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'ladder.blend')))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
clip, f = os.environ.get('REA_FRAME', 'Standing:0').split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
names = {g.index: g.name for g in src.vertex_groups}
def fam(vi):
    gs = src.data.vertices[vi].groups
    if not gs: return '-'
    n = names[max(gs, key=lambda g: g.weight).group]
    for k in ('Finger', 'Hand', 'Forearm', 'UpperArm', 'Clavicle', 'Head', 'Neck', 'Cape', 'Loin', 'Thigh', 'Calf', 'Foot', 'Toe', 'Spine', 'Pelvis'):
        if k in n: return k
    return n
me = src.data; uv = me.uv_layers.active.data
vu = np.zeros(len(me.vertices))
for p in me.polygons:
    for l in p.loop_indices: vu[me.loops[l].vertex_index] = max(vu[me.loops[l].vertex_index], uv[l].uv[0])
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); b.verts.ensure_lookup_table(); return b
bs = ev(src); fams = [fam(i) for i in range(len(bs.verts))]
for cn in sorted([o.name for o in bpy.data.objects if o.name.startswith('Cand_')], reverse=True):
    bc = ev(bpy.data.objects[cn]); tc = BVHTree.FromBMesh(bc)
    dist = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]) * 1000
    agg = collections.defaultdict(list)
    for i, dd in enumerate(dist):
        agg[fams[i]].append(dd); agg['HEADSET' if vu[i] > .5 else 'BODYSET'].append(dd)
    print('REGION', cn, clip, f, ' | '.join(f"{k} n{len(v)} p99 {np.percentile(v, 99):.1f} max {max(v):.1f}" for k, v in sorted(agg.items(), key=lambda kv: -np.percentile(kv[1], 99))), flush=True)
    bc.free()
