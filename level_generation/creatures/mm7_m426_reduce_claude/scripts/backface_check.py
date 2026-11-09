"""See-through pixels (the user's dark skirt patches: inner layers poking through the gown; the engine back-face culls
single-sided triangles, so a face seen from behind is a hole that shows whatever lies behind it): per pose and view, a
grid of orthographic rays from the camera (5 mm spacing, below 1 m) hits the posed mesh; back-facing hits are skipped
as the engine does, and a pixel counts when the first front-facing surface lies over 1 cm behind the first surface
of any facing. Prints the count per pose/view for the source Body and each candidate.
Usage: blender -b -P backface_check.py -- <ladder blend> <Cand_NN,...> [clip:frame,...]"""
import os, sys, bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
objs = {'source': bpy.data.objects['Body'], **{c: bpy.data.objects[c] for c in a[1].split(',')}}
poses = (a[2] if len(a) > 2 else 'Standing:0,Standing:24,Walking:0,Walking:6,Walking:12,Cast:10,Cast:20,Hit:6').split(',')
VIEWS = {'front': Vector((0, 1, 0)), 'front_l': Vector((-0.7, 0.7, 0)), 'front_r': Vector((0.7, 0.7, 0)), 'back': Vector((0, -1, 0))}   # ray directions
for pose in poses:
    clip, f = pose.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    row = []; seen = {}
    for name, o in objs.items():
        bm = bmesh.new(); bm.from_object(o, bpy.context.evaluated_depsgraph_get()); bm.transform(o.matrix_world); bm.normal_update()
        bm.faces.ensure_lookup_table(); tree = BVHTree.FromBMesh(bm)
        lo = np.array([min(v.co[k] for v in bm.verts) for k in range(3)]); hi = np.array([max(v.co[k] for v in bm.verts) for k in range(3)])
        res = []
        for vn, d in VIEWS.items():
            d = d.normalized(); side = d.cross(Vector((0, 0, 1))).normalized(); c = Vector(((lo + hi) / 2).tolist())
            back, hits = set(), 0
            for u in np.arange(-0.6, 0.6, 0.005):
                for z in np.arange(0.0, 1.0, 0.005):          # the skirt and legs: below 1 m
                    org = c + side * float(u) - d * 2.0; org.z = float(z)
                    loc, nrm, idx, dist = tree.ray_cast(org, d, 4.0)
                    if idx is None:
                        continue
                    hits += 1; d0 = dist; p = org; travelled = 0.0
                    while idx is not None and bm.faces[idx].normal.dot(d) > 0:
                        travelled += dist + 1e-4; p = loc + d * 1e-4
                        loc, nrm, idx, dist = tree.ray_cast(p, d, 4.0)
                    if idx is not None and travelled + dist - d0 > 0.01:
                        back.add((round(float(u), 3), round(float(z), 3)))
            res.append(f'{vn} {len(back)}')
            seen.setdefault(vn, {})[name] = back
            if os.environ.get('BF_WHERE') and name != 'source':
                extra = sorted(back - seen[vn]['source'])
                print('BFWHERE', pose, name, vn, 'only in candidate', len(extra), extra[:30])
        row.append(f'{name}: ' + ', '.join(res)); bm.free()
    print('BACKFACE', pose, ' | '.join(row), flush=True)
