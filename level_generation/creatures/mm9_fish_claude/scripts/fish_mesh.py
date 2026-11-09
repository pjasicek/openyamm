"""Stage 3 of the fish body clean: the opened signed distance (fish_open.py) -> surface mesh 'Body' (Blender Volume
to Mesh, 1 mm grid), light smoothing; the Meshy eyes are kept as 'Eyes' (mirror-symmetrised: the left eye mirrored
from the right); the Meshy pectoral fins are dropped (replaced by our own fin leaves).

Args: <in npz> <meshy fit blend> <tmp vdb> <out blend>
"""
import bpy, bmesh, sys
import numpy as np
import openvdb as vdb
argv = sys.argv[sys.argv.index('--') + 1:]
NPZ, FIT, VDB, OUT = argv
d = np.load(NPZ)
sdf, lo, vox = d['sdf'], d['lo'], float(d['vox'])
g = vdb.FloatGrid(0.0)
g.copyFromArray(np.clip(0.003 - sdf, 0, None).astype(np.float32), ijk=tuple(int(x) for x in lo), tolerance=0.0)
g.transform = vdb.createLinearTransform(voxelSize=vox)
g.name = 'density'
vdb.write(VDB, grids=[g])
bpy.ops.wm.open_mainfile(filepath=FIT)
fit = bpy.data.objects['meshy_fit']
bpy.ops.object.volume_import(filepath=VDB)
vol = bpy.context.selected_objects[0]
vol.data.render.precision = 'FULL'
print('VOLPREC', [ (g.name, g.data_type) for g in vol.data.grids])
me = bpy.data.meshes.new('Body')
body = bpy.data.objects.new('Body', me)
bpy.context.scene.collection.objects.link(body)
mod = body.modifiers.new('v2m', 'VOLUME_TO_MESH')
mod.object = vol
mod.threshold = 0.003   # density = max(0, 3 mm - sdf): the surface is sdf = 0
mod.resolution_mode = 'GRID'
mod.use_smooth_shade = True
bpy.context.view_layer.objects.active = body
bpy.ops.object.modifier_apply(modifier='v2m')
bpy.data.objects.remove(vol)
# eyes: the two separate eye components of the Meshy return (centre y < -0.1), symmetric copy of the right eye
bm = bmesh.new(); bm.from_mesh(fit.data)
comp = fit.data.attributes['comp']
bm.faces.ensure_lookup_table()
cl = bm.faces.layers.int.get('comp')
eyes_faces = {}
for f in bm.faces:
    c = f[cl]
    if c == 0:
        continue
    cy = sum(v.co.y for v in f.verts) / len(f.verts)
    eyes_faces.setdefault(c, []).append(f)
eye_comps = [c for c, fs in eyes_faces.items() if sum(v.co.y for f in fs for v in f.verts) / sum(len(f.verts) for f in fs) < -0.1]
right = min(eye_comps, key=lambda c: sum(v.co.x for f in eyes_faces[c] for v in f.verts))  # -x = the fish's right
keep = set(eyes_faces[right])
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context='FACES')
mir = bm.copy()
for v in mir.verts:
    v.co.x = -v.co.x
bmesh.ops.reverse_faces(mir, faces=mir.faces)
me2 = bpy.data.meshes.new('Eyes')
bm.to_mesh(me2)
tmp = bpy.data.meshes.new('tmp'); mir.to_mesh(tmp)
eyes = bpy.data.objects.new('Eyes', me2); bpy.context.scene.collection.objects.link(eyes)
t2 = bpy.data.objects.new('tmp', tmp); bpy.context.scene.collection.objects.link(t2)
for o in bpy.data.objects:
    o.select_set(o in (eyes, t2))
bpy.context.view_layer.objects.active = eyes
bpy.ops.object.join()
bpy.data.objects.remove(fit)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.attributes.get('comp'):
        o.data.attributes.remove(o.data.attributes['comp'])
print('MESHED', len(body.data.vertices), len(body.data.polygons), 'eyes', len(eyes.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
