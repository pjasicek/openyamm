"""Head-only Meshy model on the body. The old head (part 2) goes; the new one-skin head (face, neck, hair: part 20) and eyes (22) sit crown at MM9's height, neck centred in the body's collar. The body's standing collar is Meshy's
own, part of the doublet. Args: <fit blend> <head blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
CROWN = 0.964; NECK_Y = 0.052; BASE_Z = 0.6; FLARE = 1.5; NECK_TOP = 0.70
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 20, 'Eyes': 22}
F = np.array([v.co[:] for v in parts['Face'].data.vertices])
nk = F[F[:, 2] < -0.115]
off = Vector((0, NECK_Y - 0.5 * (nk[:, 1].min() + nk[:, 1].max()), CROWN - F[:, 2].max()))
print('GRAFT off', [round(x, 4) for x in off], 'neck ring x', nk[:, 0].min().round(3), nk[:, 0].max().round(3), 'y', nk[:, 1].min().round(3), nk[:, 1].max().round(3))
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.faces.layers.int['part']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] == 2], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts: v.co += off
    if nm == 'Face':
        bd = [e for e in t.edges if e.is_boundary]
        print('GRAFT boundary', len(bd))
        # the closed neck base reaches down and out under the collar, so no gap shows in the V at the throat
        vs = [v for v in t.verts if v.co.z < NECK_TOP and abs(v.co.x) < 0.075]
        z0 = min(v.co.z for v in vs); c = Vector((0, NECK_Y, 0))
        for v in vs:
            u = (NECK_TOP - v.co.z) / (NECK_TOP - z0)
            k = 1 + (FLARE - 1) * u * u
            v.co = Vector((v.co.x * k, c.y + (v.co.y - c.y) * k, NECK_TOP - (NECK_TOP - BASE_Z) * u))
    tl = t.faces.layers.int.new('part')
    for f in t.faces: f[tl] = pid[nm]
    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    bpy.data.meshes.remove(tm)
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons: p.use_smooth = True
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
c = np.array([v.co[:] for v in body.data.vertices])
print('FINAL verts', len(c), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'bbox', c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
