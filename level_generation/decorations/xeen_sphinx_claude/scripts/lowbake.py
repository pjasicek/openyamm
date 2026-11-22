"""Stage 3 (Blender): LOD0 (LowBody + LowFace joined, one material), atlas UVs (claude_shared/uv_atlas.py: PartUV
charts, seam pass, sparrow packing; the front parts seen up close at the door and the head denser) and the Cycles
bakes the numpy stage composes into maps:
  bake_normal.png  2048, tangent normal from the high meshes (the striped SDF surface with egywalh grain as bump,
                   the grafted face with its own normal map), selected to active; misses stay black
  bake_ao_big.png  2048, ambient occlusion over 4 m (with a ground plane at z 0)
  bake_ao_small.png 2048, ambient occlusion over 0.6 m (crevices)
  tris.npz         per triangle: glTF v-down UVs, positions (model units: x, f, z) and vertex normals, the part
                   (0 body, 1 face), for finish_maps.py and gutter_fill
Writes work/<id>/low.blend. Usage: blender -b --python lowbake.py -- <id>"""
import json
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared'))
sys.path.insert(0, HERE)
import uv_atlas  # noqa: E402
import sphinx_sdf  # noqa: E402

sid = sys.argv[sys.argv.index('--') + 1]
cfg = json.load(open(os.path.join(HERE, 'sphinx.json')))[sid]
work = os.path.join(PROJECT, 'work', sid)
SIZE = 2048
bpy.ops.wm.open_mainfile(filepath=os.path.join(work, 'mesh.blend'))
scene = bpy.context.scene
high_body = bpy.data.objects['HighBody']
high_face = bpy.data.objects['HighFace']


def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


bm = bmesh.new()
bm.from_mesh(bpy.data.objects['LowBody'].data)
part = bm.faces.layers.int.new('part')
n_body = len(bm.faces)
bm.from_mesh(bpy.data.objects['LowFace'].data)
bm.faces.ensure_lookup_table()
for f in bm.faces[n_body:]:
    f[part] = 1
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
for layer in list(bm.verts.layers.deform):     # the peasant's bone weights (stale group indices)
    bm.verts.layers.deform.remove(layer)
me = bpy.data.meshes.new('LOD0')
bm.to_mesh(me)
bm.free()
me.shade_smooth()
me.materials.clear()
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
low = bpy.data.objects.new('LOD0', me)
scene.collection.objects.link(low)
for name in ('LowBody', 'LowFace'):
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
print('LOD0 triangles', tris(me))

co = np.array([v.co for v in me.vertices]) * 100.0
X, F, Z = co[:, 0], -co[:, 1], co[:, 2]
_, d_body, d_head = sphinx_sdf.full_sdf(X, F, Z, cfg)
is_head = np.abs(d_head) < np.abs(d_body)
face_verts = set()
parts = np.zeros(len(me.polygons), np.int32)
me.attributes['part'].data.foreach_get('value', parts)
for p, poly in zip(parts, me.polygons):
    if p == 1:
        face_verts.update(poly.vertices)
# regions: one group per vertex (PartUV's part tree reads them as skin weights) and density classes by region
region = np.full(len(co), 'Rest', object)
for name, rule in cfg['regions']:
    sel = np.ones(len(co), bool)
    for key, val in rule.items():
        sel &= {'f>': F > val, 'f<': F <= val, 'x>': X > val, 'x<': X < val, 'z<': Z < val, 'z>': Z > val,
                '|x|<': np.abs(X) < val}[key]
    region[sel & (region == 'Rest')] = name
region[is_head] = 'Head'
region[sorted(face_verts)] = 'Face'
groups = {}
for name in sorted(set(region)):
    groups[name] = low.vertex_groups.new(name=name)
    groups[name].add([int(i) for i in np.nonzero(region == name)[0]], 1.0, 'REPLACE')
print('REGIONS', {k: int((region == k).sum()) for k in groups})
report = uv_atlas.unwrap(low, group_factors=cfg['density'], margin_px=4, size=SIZE, sparrow_seconds=30,
                         sparrow_runs=3)
print('UV charts', report.get('charts_used'), 'packer', report.get('packer_used'), 'fallbacks', report.get('fallbacks'))
print('UV report', {k: report[k] for k in report if k in ('atlas', 'islands', 'stretch_p90', 'density_spread')})
json.dump({k: v for k, v in report.items() if isinstance(v, (int, float, str, list, dict))},
          open(os.path.join(work, 'uv_report.json'), 'w'), indent=1, default=str)

mat = bpy.data.materials.new('SphinxBake')
mat.use_nodes = True
target = mat.node_tree.nodes.new('ShaderNodeTexImage')
mat.node_tree.nodes.active = target
me.materials.append(mat)


def image(name):
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color'
    return img


def save(img, path):
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    print('BAKED', path)


scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 12
scene.cycles.samples = 16
scene.render.bake.use_selected_to_active = True
scene.render.bake.cage_extrusion = 0.15
scene.render.bake.max_ray_distance = 0.45
scene.render.bake.margin = 0
for o in scene.objects:
    o.select_set(o in (high_body, high_face))
low.select_set(True)
for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter',
             'visible_shadow'):
    setattr(low, attr, False)
bpy.context.view_layer.objects.active = low
target.image = image('bake_normal')
bpy.ops.object.bake(type='NORMAL')
save(target.image, os.path.join(work, 'bake_normal.png'))

# AO on the low itself, over a ground plane at z 0
scene.render.bake.use_selected_to_active = False
scene.render.bake.margin = 8
for o in (high_body, high_face):
    o.hide_render = True
    o.select_set(False)
for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter',
             'visible_shadow'):
    setattr(low, attr, True)
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
ground = bpy.context.active_object
ground.select_set(False)
low.select_set(True)
bpy.context.view_layer.objects.active = low
if scene.world is None:
    scene.world = bpy.data.worlds.new('w')
scene.cycles.samples = 64
for dist, name in ((4.0, 'bake_ao_big'), (0.6, 'bake_ao_small')):
    scene.world.light_settings.distance = dist
    target.image = image(name)
    bpy.ops.object.bake(type='AO')
    save(target.image, os.path.join(work, name + '.png'))
bpy.data.objects.remove(ground, do_unlink=True)

# triangles for the numpy stage (parts read again: the UV weld may have touched the mesh)
parts = np.zeros(len(me.polygons), np.int32)
me.attributes['part'].data.foreach_get('value', parts)
uv = np.zeros((len(me.loops), 2), np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', uv.ravel())
vco = np.array([v.co for v in me.vertices], np.float64)
me.calc_loop_triangles()
loop_v = np.array([l.vertex_index for l in me.loops])
nrm = np.zeros((len(me.loops), 3), np.float32)
me.corner_normals.foreach_get('vector', nrm.ravel())
tri_loops = np.array([p.loop_indices for p in me.polygons])
tri_uv = uv[tri_loops].copy()
tri_uv[..., 1] = 1.0 - tri_uv[..., 1]
pos = vco[loop_v[tri_loops]] * 100.0
pos = np.stack([pos[..., 0], -pos[..., 1], pos[..., 2]], -1)
n = nrm[tri_loops]
n = np.stack([n[..., 0], -n[..., 1], n[..., 2]], -1)
np.savez(os.path.join(work, 'tris.npz'), uv=tri_uv, pos=pos.astype(np.float32), nrm=n.astype(np.float32),
         part=parts.astype(np.int8))
target.image = None
low.vertex_groups.clear()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'low.blend'))
print('LOWBAKE_DONE')
