"""Stage 2 (Blender): LOD0 atlas UVs and the Cycles bakes the numpy stage composes into maps.

- UVs: claude_shared/uv_atlas.py (PartUV charts, seam pass, sparrow packing, 4-texel margin); the face denser
  (`face_uv_factor`), the rest one density.
- bake_normal.png  2048, tangent normal from High (with the egywalh grain as bump, box projected), selected to active
- bake_ao_big.png  2048, ambient occlusion over 2 m with a ground plane at z 0
- bake_ao_small.png 2048, ambient occlusion over 0.35 m (crevices: eye sockets, mouth, cracks)
- tris.npz  per triangle: glTF v-down UVs, positions (units, x / forward / z) and corner normals, the face flag
Writes work/low.blend. Usage: blender -b --python lowbake.py"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared'))
import uv_atlas  # noqa: E402

cfg = json.load(open(os.path.join(HERE, 'boulder.json')))
work = os.path.join(PROJECT, 'work')
GRAIN = os.path.join(REPO, 'assets_source', 'worlds', 'mm6', 'textures_x4', 'egywalh.png')
SIZE = 2048
bpy.ops.wm.open_mainfile(filepath=os.path.join(work, 'mesh.blend'))
scene = bpy.context.scene
high = bpy.data.objects['High']
low = bpy.data.objects['Low']
for o in list(scene.objects):
    if o not in (high, low):
        bpy.data.objects.remove(o, do_unlink=True)
low.name = 'LOD0'
me = low.data
me.materials.clear()
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
face_group = low.vertex_groups['Face']
face_verts = np.zeros(len(me.vertices), bool)
for v in me.vertices:
    face_verts[v.index] = any(g.group == face_group.index for g in v.groups)
rest = low.vertex_groups.new(name='Rest')
rest.add([int(i) for i in np.nonzero(~face_verts)[0]], 1.0, 'REPLACE')
report = uv_atlas.unwrap(low, group_factors={'Face': cfg['face_uv_factor'], 'Rest': 1.0}, margin_px=4, size=SIZE,
                         sparrow_seconds=30, sparrow_runs=3)
print('UV charts', report.get('charts_used'), 'packer', report.get('packer_used'), 'fallbacks', report.get('fallbacks'))
print('UV report', {k: report[k] for k in report if k in ('atlas', 'islands', 'stretch_p90', 'density_spread')})
json.dump({k: v for k, v in report.items() if isinstance(v, (int, float, str, list, dict))},
          open(os.path.join(work, 'uv_report.json'), 'w'), indent=1, default=str)
me = low.data
face_verts = np.zeros(len(me.vertices), bool)
for v in me.vertices:
    face_verts[v.index] = any(g.group == face_group.index for g in v.groups)

# the high's stone grain: egywalh as bump (box projected, two scales), picked up by the normal bake
m = bpy.data.materials.new('HighStone')
m.use_nodes = True
nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tc = nt.nodes.new('ShaderNodeTexCoord')
acc = None
for scale, weight in ((1 / 1.28, 0.6), (1 / 0.48, 0.4)):
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(GRAIN, check_existing=True)
    tx.image.colorspace_settings.name = 'Non-Color'
    tx.projection = 'BOX'
    tx.projection_blend = 0.3
    nt.links.new(mp.outputs[0], tx.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = weight
    nt.links.new(tx.outputs['Color'], mul.inputs[0])
    if acc is None:
        acc = mul.outputs[0]
    else:
        add = nt.nodes.new('ShaderNodeMath')
        nt.links.new(acc, add.inputs[0])
        nt.links.new(mul.outputs[0], add.inputs[1])
        acc = add.outputs[0]
bump = nt.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.4
bump.inputs['Distance'].default_value = 0.02
nt.links.new(acc, bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
high.data.materials.clear()
high.data.materials.append(m)

mat = bpy.data.materials.new('BoulderBake')
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


VIS = ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter',
       'visible_shadow')
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 12
scene.cycles.samples = 16
scene.render.bake.use_selected_to_active = True
scene.render.bake.cage_extrusion = 0.08
scene.render.bake.max_ray_distance = 0.2
scene.render.bake.margin = 0
for o in scene.objects:
    o.select_set(o is high)
low.select_set(True)
for attr in VIS:
    setattr(low, attr, False)
bpy.context.view_layer.objects.active = low
target.image = image('bake_normal')
bpy.ops.object.bake(type='NORMAL')
save(target.image, os.path.join(work, 'bake_normal.png'))

# AO on the low itself, over a ground plane at z 0
scene.render.bake.use_selected_to_active = False
scene.render.bake.margin = 8
high.hide_render = True
high.select_set(False)
for attr in VIS:
    setattr(low, attr, True)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = bpy.context.active_object
ground.select_set(False)
low.select_set(True)
bpy.context.view_layer.objects.active = low
if scene.world is None:
    scene.world = bpy.data.worlds.new('w')
scene.cycles.samples = 96
for dist, name in ((2.0, 'bake_ao_big'), (0.35, 'bake_ao_small')):
    scene.world.light_settings.distance = dist
    target.image = image(name)
    bpy.ops.object.bake(type='AO')
    save(target.image, os.path.join(work, name + '.png'))
bpy.data.objects.remove(ground, do_unlink=True)

uv = np.zeros((len(me.loops), 2), np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', uv.ravel())
vco = np.array([v.co for v in me.vertices], np.float64)
loop_v = np.array([lp.vertex_index for lp in me.loops])
nrm = np.zeros((len(me.loops), 3), np.float32)
me.corner_normals.foreach_get('vector', nrm.ravel())
tri_loops = np.array([p.loop_indices for p in me.polygons])
tri_uv = uv[tri_loops].copy()
tri_uv[..., 1] = 1.0 - tri_uv[..., 1]
pos = vco[loop_v[tri_loops]] * 100.0
pos = np.stack([pos[..., 0], -pos[..., 1], pos[..., 2]], -1)          # x, forward (the face's way), z
n = nrm[tri_loops]
n = np.stack([n[..., 0], -n[..., 1], n[..., 2]], -1)
is_face = face_verts[loop_v[tri_loops]].all(1)
np.savez(os.path.join(work, 'tris.npz'), uv=tri_uv, pos=pos.astype(np.float32), nrm=n.astype(np.float32),
         face=is_face.astype(np.int8))
target.image = None
for o in list(scene.objects):
    if o is not low:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'low.blend'))
print('LOWBAKE_DONE')
