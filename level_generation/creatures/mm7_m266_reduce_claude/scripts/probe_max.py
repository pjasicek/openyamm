"""Where the ladder's max error sits: top vertex->surface distances of each candidate against the source at the
worst frames, with the dominant bone of the nearest source vertex. Usage: blender -b -P probe_max.py"""
import os, bpy, bmesh
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
names = {g.index: g.name for g in src.vertex_groups}
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
def bone(vi):
    gs = [g for g in src.data.vertices[vi].groups if names[g.group] != 'ReduceProtect']
    return max(gs, key=lambda g: g.weight) if gs else None
for clip, f in [(c.split(':')[0], int(c.split(':')[1])) for c in os.environ.get('REA_FRAMES', 'Death:45,Death:21,Standing:0').split(',')]:
    rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(f)
    bs = ev(src); ts = BVHTree.FromBMesh(bs)
    for cn in [o.name for o in bpy.data.objects if o.name.startswith('Cand_')]:
        bc = ev(bpy.data.objects[cn]); tc = BVHTree.FromBMesh(bc)
        d1 = [(ts.find_nearest(v.co)[3], 'cand', v.co.copy()) for v in bc.verts]
        d2 = [(tc.find_nearest(v.co)[3], 'src', v.co.copy(), v.index) for v in bs.verts]
        top = sorted(d1 + d2, key=lambda x: -x[0])[:3]
        out = []
        for t in top:
            co = t[2]; vi = t[3] if t[1] == 'src' else min(range(len(bs.verts)), key=lambda i: (bs.verts[i].co - co).length)
            g = bone(vi); out.append(f"{t[0]*1000:.1f}mm {t[1]} at ({co.x:.2f},{co.y:.2f},{co.z:.2f}) {names[g.group] if g else '-'}")
        print('PROBE', clip, f, cn, ' | '.join(out), flush=True)
        bc.free()
    bs.free()
