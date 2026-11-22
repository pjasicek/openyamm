"""Stage 2 (Blender): LOD0 from the high statue (decimated figure + plinth, one material), atlas UVs
(claude_shared/uv_atlas.py) and bakes from the high statue: tangent normal (the source creature's own normal maps
carried over as carved detail), basalt colour (vlcwl3a grain on a near-black ramp, grey-brown weathering, AO and
cavity darkening, ash in crevices and on top faces) and roughness. Writes work/<id>/low.blend, bake_color.png
(2048, sRGB), bake_normal.png (2048), bake_rough.png (1024) and uv.npz (glTF v-down UV triangles for gutter_fill).
Usage: blender -b --python lowbake.py -- <id>"""
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
import uv_atlas  # noqa: E402

idol_id = sys.argv[sys.argv.index('--') + 1]
cfg = json.load(open(os.path.join(HERE, 'idols.json')))[idol_id]
work = os.path.join(PROJECT, 'work', idol_id)
STONE_TEX = os.path.join(REPO, 'assets_source', 'worlds', 'mm6', 'textures_x4', 'vlcwl3a.png')
bpy.ops.wm.open_mainfile(filepath=os.path.join(work, 'high.blend'))
scene = bpy.context.scene
fig = bpy.data.objects['HighFigure']
plinth = bpy.data.objects['HighPlinth']


def tris(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def decimated(obj, target):
    tmp = bpy.data.objects.new('tmp', obj.data.copy())
    scene.collection.objects.link(tmp)
    mod = tmp.modifiers.new('dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = min(1.0, target / tris(tmp.data))
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    return me


fig_low = decimated(fig, cfg['lod0_figure_tris'])
bm = bmesh.new()
bm.from_mesh(fig_low)
part = bm.faces.layers.int.new('part')
n_fig = len(bm.faces)
bm.from_mesh(plinth.data)
bm.faces.ensure_lookup_table()
for f in bm.faces[n_fig:]:
    f[part] = 1
bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY')
for f in bm.faces:
    f.material_index = 0
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
me = bpy.data.meshes.new('LOD0')
bm.to_mesh(me)
bm.free()
me.shade_smooth()
me.set_sharp_from_angle(angle=1.047198)   # hard plinth corners and spike ridges above 60 degrees
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
for a in [a for a in me.attributes if a.name.startswith('Col') or a.domain == 'CORNER' and a.data_type == 'BYTE_COLOR']:
    me.attributes.remove(a)
low = bpy.data.objects.new('LOD0', me)
scene.collection.objects.link(low)
print('LOD0 triangles', tris(me), 'figure', tris(fig_low))
# The figure gets 1.7x the plinth's linear texel density (uv_atlas head_groups).
parts = [0] * len(me.polygons)
me.attributes['part'].data.foreach_get('value', parts)
groups = {0: low.vertex_groups.new(name='Figure'), 1: low.vertex_groups.new(name='Plinth')}
for p, poly in zip(parts, me.polygons):
    groups[p].add(list(poly.vertices), 1.0, 'REPLACE')
report = uv_atlas.unwrap(low, head_groups=('Figure',), head_factor=1.7, margin_px=4, size=2048, sparrow_seconds=20,
                         sparrow_runs=3)
print('UV charts', report.get('charts_used'), 'packer', report.get('packer_used'), 'fallbacks', report.get('fallbacks'))
print('UV report', {k: report[k] for k in report if k in ('atlas', 'islands', 'stretch_p90', 'density_spread')})

# Bake target material on the low statue.
mat = bpy.data.materials.new('IdolStone')
mat.use_nodes = True
target = mat.node_tree.nodes.new('ShaderNodeTexImage')
mat.node_tree.nodes.active = target
me.materials.clear()
me.materials.append(mat)


def image(name, size, non_color):
    img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.render.bake.use_selected_to_active = True
scene.render.bake.cage_extrusion = 0.06
scene.render.bake.max_ray_distance = 0.18
scene.render.bake.margin = 0          # misses stay black; finish_maps.py turns them flat
scene.render.bake.margin_type = 'EXTEND'
for o in scene.objects:
    o.select_set(o in (fig, plinth))
low.select_set(True)
# the bake target must not occlude the high statue's AO rays
for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter',
             'visible_shadow'):
    setattr(low, attr, False)
bpy.context.view_layer.objects.active = low


def bake(kind, img, path, node=None):
    (node or target).image = img
    bpy.ops.object.bake(type=kind)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    print('BAKED', kind, path)


# 1. Normal: the high figure keeps its imported materials (their normal maps).
bake('NORMAL', image('bake_normal', 2048, True), os.path.join(work, 'bake_normal.png'))


# 2./3. Colour and roughness: an emission shader on every high material slot.
def stone_material(name, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    L = nt.links
    for n in list(N):
        N.remove(n)
    out = N.new('ShaderNodeOutputMaterial')
    emit = N.new('ShaderNodeEmission')
    L.new(emit.outputs[0], out.inputs['Surface'])
    tc = N.new('ShaderNodeTexCoord')
    geo = N.new('ShaderNodeNewGeometry')

    def math(op, a, b=None, clamp=False):
        n = N.new('ShaderNodeMath')
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    def grain(scale):
        mp = N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale, scale, scale * 0.5)
        L.new(tc.outputs['Object'], mp.inputs['Vector'])
        tx = N.new('ShaderNodeTexImage')
        tx.image = bpy.data.images.load(STONE_TEX, check_existing=True)
        tx.projection = 'BOX'
        tx.projection_blend = 0.35
        L.new(mp.outputs[0], tx.inputs['Vector'])
        bw = N.new('ShaderNodeRGBToBW')
        L.new(tx.outputs['Color'], bw.inputs[0])
        return bw.outputs[0]

    # grain: two scales of the volcanic stone (0.55 and 1.4 tiles per metre) averaged against tiling
    g = math('ADD', math('MULTIPLY', grain(0.55), 0.6), math('MULTIPLY', grain(1.4), 0.4))
    noise = N.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 0.35
    noise.inputs['Detail'].default_value = 4.0
    L.new(tc.outputs['Object'], noise.inputs['Vector'])
    weather = N.new('ShaderNodeMapRange')
    weather.inputs['From Min'].default_value = 0.42
    weather.inputs['From Max'].default_value = 0.68
    L.new(noise.outputs['Fac'], weather.inputs['Value'])
    ao_big = N.new('ShaderNodeAmbientOcclusion')
    ao_big.inputs['Distance'].default_value = 0.6
    ao_big.samples = 16
    ao_small = N.new('ShaderNodeAmbientOcclusion')
    ao_small.inputs['Distance'].default_value = 0.08
    ao_small.samples = 16
    up = N.new('ShaderNodeSeparateXYZ')
    L.new(geo.outputs['Normal'], up.inputs[0])
    top = N.new('ShaderNodeMapRange')
    top.inputs['From Min'].default_value = 0.5
    top.inputs['From Max'].default_value = 0.92
    L.new(up.outputs['Z'], top.inputs['Value'])
    crevice = math('SUBTRACT', 1.0, ao_small.outputs['AO'], clamp=True)
    if roughness:
        r = math('ADD', 0.80, math('MULTIPLY', math('SUBTRACT', g, 0.35), 0.12))
        r = math('ADD', r, math('MULTIPLY', top.outputs[0], 0.08))
        r = math('ADD', r, math('MULTIPLY', crevice, 0.06), clamp=True)
        L.new(r, emit.inputs['Color'])
        return m
    ramp = N.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.022, 0.021, 0.022, 1)
    cr.elements[1].position = 1.0
    cr.elements[1].color = (0.20, 0.188, 0.172, 1)
    mid = cr.elements.new(0.45)
    mid.color = (0.060, 0.057, 0.054, 1)
    L.new(g, ramp.inputs['Fac'])
    # grey-brown weathering: patches lifted toward a warm grey
    wf = math('MULTIPLY', weather.outputs[0], 0.55)
    tint = N.new('ShaderNodeCombineXYZ')
    for c, k in (('X', 0.55), ('Y', 0.32), ('Z', 0.12)):
        L.new(math('ADD', 1.0, math('MULTIPLY', wf, k)), tint.inputs[c])
    weathered = N.new('ShaderNodeVectorMath')
    weathered.operation = 'MULTIPLY'
    L.new(ramp.outputs['Color'], weathered.inputs[0])
    L.new(tint.outputs[0], weathered.inputs[1])
    occl = math('MULTIPLY', math('ADD', 0.38, math('MULTIPLY', ao_big.outputs['AO'], 0.62)),
                math('ADD', 0.5, math('MULTIPLY', ao_small.outputs['AO'], 0.5)))
    shaded = N.new('ShaderNodeVectorMath')
    shaded.operation = 'SCALE'
    L.new(weathered.outputs[0], shaded.inputs[0])
    L.new(occl, shaded.inputs['Scale'])
    # ash: pale grey dust in crevices facing up and on top faces, broken by the noise
    upish = math('MAXIMUM', math('MULTIPLY', math('ADD', up.outputs['Z'], 0.3), 0.8), 0.0)
    ash_amt = math('ADD', math('MULTIPLY', math('MULTIPLY', crevice, upish), 0.55),
                   math('MULTIPLY', math('MULTIPLY', top.outputs[0], noise.outputs['Fac']), 0.30), clamp=True)
    ash = N.new('ShaderNodeMix')
    ash.data_type = 'RGBA'
    L.new(ash_amt, ash.inputs['Factor'])
    L.new(shaded.outputs[0], ash.inputs['A'])
    ash.inputs['B'].default_value = (0.115, 0.108, 0.100, 1)
    floor = N.new('ShaderNodeMix')
    floor.data_type = 'RGBA'
    floor.blend_type = 'LIGHTEN'
    floor.inputs['Factor'].default_value = 1.0
    L.new(ash.outputs['Result'], floor.inputs['A'])
    floor.inputs['B'].default_value = (0.0125, 0.0125, 0.0135, 1)
    L.new(floor.outputs['Result'], emit.inputs['Color'])
    return m


# 2./3. Colour and roughness are evaluated on the low statue itself (its own AO), not projected from the high one:
# projection misses on thin claws and spikes streaked the first bake.
scene.render.bake.use_selected_to_active = False
scene.render.bake.margin = 16
for o in (fig, plinth):
    o.hide_render = True
    o.select_set(False)
for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter',
             'visible_shadow'):
    setattr(low, attr, True)
for img, path, rough in ((image('bake_color', 2048, False), 'bake_color.png', False),
                         (image('bake_rough', 1024, True), 'bake_rough.png', True)):
    sm = stone_material('BakeRough' if rough else 'BakeStone', rough)
    node = sm.node_tree.nodes.new('ShaderNodeTexImage')
    sm.node_tree.nodes.active = node
    me.materials[0] = sm
    bake('EMIT', img, os.path.join(work, path), node)
me.materials[0] = mat

# UV triangles for gutter_fill (glTF v-down)
uv = np.zeros((len(me.loops), 2), np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', uv.ravel())
tri_uv = np.array([[uv[li] for li in p.loop_indices] for p in me.polygons], np.float32)
tri_uv[..., 1] = 1.0 - tri_uv[..., 1]
np.savez(os.path.join(work, 'uv.npz'), uv=tri_uv)
target.image = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'low.blend'))
print('LOWBAKE_DONE')
