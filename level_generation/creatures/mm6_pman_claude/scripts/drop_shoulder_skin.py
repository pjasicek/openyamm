"""Delete Body faces that are seen just in front of the Tunic (< 8 mm) around the collar points, sampled with
front and three-quarter view rays: the residual skin poke-through on the shoulder tops."""
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
m = bpy.data.objects['Peasant']; PARTS = json.loads(bpy.context.scene['pfem_parts'])
bm = bmesh.new(); bm.from_mesh(m.data); bm.faces.ensure_lookup_table()
pl = bm.faces.layers.int.get('part')
V = [v.co.copy() for v in bm.verts]
T, B = PARTS.index('Tunic'), PARTS.index('Body')
tf = [f for f in bm.faces if f[pl] == T]; bf = [f for f in bm.faces if f[pl] == B]
tt = BVHTree.FromPolygons(V, [tuple(v.index for v in f.verts) for f in tf])
bt = BVHTree.FromPolygons(V, [tuple(v.index for v in f.verts) for f in bf])
kill = set()
for yaw in (-50, -25, 0, 25, 50):
    for pitch in (0, 20, 40):
        a, p = math.radians(yaw), math.radians(pitch)
        d = Vector((math.sin(a) * math.cos(p), math.cos(a) * math.cos(p), -math.sin(p)))
        for x in np.linspace(-0.16, 0.16, 81):
            if abs(x) < 0.05:
                continue
            for z in np.linspace(1.28, 1.38, 41):
                o = Vector((x, 0.0, z)) - d * 0.6
                hb = bt.ray_cast(o, d, 1.2); ht = tt.ray_cast(o, d, 1.2)
                if hb[0] is not None and ht[0] is not None and 0 < ht[3] - hb[3] < 0.008:
                    kill.add(bf[hb[2]].index)
faces = [bm.faces[i] for i in kill]
bmesh.ops.delete(bm, geom=faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(m.data); bm.free()
print('DROPPED shoulder skin faces', len(faces))
bpy.ops.wm.save_mainfile()
