"""Source vertices farther than REA_MM from a candidate's surface at given frames (both evaluated):
prints count, dominant bones and welded components; saves work/err_<cand>.npy (source vertex indices).
Usage: REA_CAND=Cand_70 REA_FRAMES=Death:12 REA_MM=12 blender -b work/ladder.blend -P err_verts.py"""
import os, bpy, bmesh, collections, numpy as np
from mathutils.bvhtree import BVHTree
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
names = {g.index: g.name for g in src.vertex_groups}
cand = bpy.data.objects[os.environ['REA_CAND']]; lim = float(os.environ.get('REA_MM', '12')) / 1000
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
bad = set()
for cf in os.environ.get('REA_FRAMES', 'Death:12').split(','):
    clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    bs = ev(src); tc = BVHTree.FromBMesh(ev(cand))
    hit = [v.index for v in bs.verts if tc.find_nearest(v.co)[3] > lim]; bad |= set(hit)
    print('ERR', cf, len(hit))
bones = collections.Counter(names[max(src.data.vertices[i].groups, key=lambda g: g.weight).group] for i in bad)
print('ERR bones', bones.most_common(10))
co = np.array([src.data.vertices[i].co[:] for i in sorted(bad)])
if len(co): print('ERR rest bbox', co.min(0).round(3), co.max(0).round(3))
np.save(f"work/err_{cand.name}.npy", np.array(sorted(bad)))
