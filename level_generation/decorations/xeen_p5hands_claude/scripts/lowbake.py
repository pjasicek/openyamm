"""Stage 2 (Blender): LOD0 from the high stone hand (collapse decimation), atlas UVs (claude_shared/uv_atlas.py) and
bakes: tangent normal from the high hand, a pale ivory marble with gold veins (MM7 7tws1h grain on an ivory ramp, the
veins of MM9's marb94orui as gold, AO and cavity darkening) and roughness, both evaluated on the low hand itself.
Adapted from xeen_idols_claude/scripts/lowbake.py. Writes work/low.blend, bake_color.png (2048, sRGB),
bake_normal.png (2048), bake_rough.png (1024), uv.npz. Usage: blender -b --python lowbake.py"""
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

cfg = json.load(open(os.path.join(HERE, 'hand.json')))
work = os.path.join(PROJECT, 'work')
STONE_TEX = os.path.join(REPO, 'assets_source', 'worlds', 'mm7', 'textures_x4', '7tws1h.png')
VEIN_TEX = os.path.join(REPO, 'assets_source', 'worlds', 'mm9', 'textures_x4', 'marb94orui.png')
bpy.ops.wm.open_mainfile(filepath=os.path.join(work, 'high.blend'))
scene = bpy.context.scene
fig = bpy.data.objects['HighHand']


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


fig_low = decimated(fig, cfg['lod0_tris'])
bm = bmesh.new()
bm.from_mesh(fig_low)
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
me = bpy.data.meshes.new('LOD0')
bm.to_mesh(me)
bm.free()
me.shade_smooth()
me.set_sharp_from_angle(angle=1.047198)
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
low = bpy.data.objects.new('LOD0', me)
scene.collection.objects.link(low)
print('LOD0 triangles', tris(me))
report = uv_atlas.unwrap(low, margin_px=4, size=2048, sparrow_seconds=25, sparrow_runs=7)
print('UV charts', report.get('charts_used'), 'packer', report.get('packer_used'), 'fallbacks', report.get('fallbacks'))
print('UV report', {k: report[k] for k in report if k in ('atlas', 'islands', 'stretch_p90', 'density_spread')})

# Bake target material on the low statue.
mat = bpy.data.materials.new('HandStone')
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
scene.render.bake.cage_extrusion = 0.012
scene.render.bake.max_ray_distance = 0.03
scene.render.bake.margin = 0          # misses stay black; finish_maps.py turns them flat
scene.render.bake.margin_type = 'EXTEND'
for o in scene.objects:
    o.select_set(o is fig)
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

    def tex_bw(path, scale, offset=(0, 0, 0)):
        mp = N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale, scale, scale)
        mp.inputs['Location'].default_value = offset
        L.new(tc.outputs['Object'], mp.inputs['Vector'])
        tx = N.new('ShaderNodeTexImage')
        tx.image = bpy.data.images.load(path, check_existing=True)
        tx.image.colorspace_settings.name = 'Non-Color'      # grain and veins as their stored (sRGB) values
        tx.projection = 'BOX'
        tx.projection_blend = 0.35
        L.new(mp.outputs[0], tx.inputs['Vector'])
        bw = N.new('ShaderNodeRGBToBW')
        L.new(tx.outputs['Color'], bw.inputs[0])
        return bw.outputs[0]

    g = math('ADD', math('MULTIPLY', tex_bw(STONE_TEX, 2.2), 0.6), math('MULTIPLY', tex_bw(STONE_TEX, 5.0), 0.4))
    vr = N.new('ShaderNodeMapRange')
    vr.inputs['From Min'].default_value = 0.30
    vr.inputs['From Max'].default_value = 0.55
    L.new(tex_bw(VEIN_TEX, 2.4, (0.31, 0.17, 0.05)), vr.inputs['Value'])
    vein = vr.outputs[0]
    ao_big = N.new('ShaderNodeAmbientOcclusion')
    ao_big.inputs['Distance'].default_value = 0.22
    ao_big.samples = 16
    ao_small = N.new('ShaderNodeAmbientOcclusion')
    ao_small.inputs['Distance'].default_value = 0.025
    ao_small.samples = 16
    crevice = math('SUBTRACT', 1.0, ao_small.outputs['AO'], clamp=True)
    if roughness:
        r = math('ADD', 0.50, math('MULTIPLY', math('SUBTRACT', g, 0.45), 0.25))
        r = math('SUBTRACT', r, math('MULTIPLY', vein, 0.18))
        r = math('ADD', r, math('MULTIPLY', crevice, 0.25), clamp=True)
        L.new(r, emit.inputs['Color'])
        return m
    ramp = N.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.24
    cr.elements[0].color = (0.56, 0.47, 0.32, 1)
    cr.elements[1].position = 0.54
    cr.elements[1].color = (0.92, 0.85, 0.68, 1)
    L.new(g, ramp.inputs['Fac'])
    gold = N.new('ShaderNodeMix')
    gold.data_type = 'RGBA'
    L.new(math('MULTIPLY', vein, 0.95), gold.inputs['Factor'])
    L.new(ramp.outputs['Color'], gold.inputs['A'])
    gold.inputs['B'].default_value = (0.62, 0.40, 0.08, 1)
    occl = math('MULTIPLY', math('ADD', 0.62, math('MULTIPLY', ao_big.outputs['AO'], 0.38)),
                math('ADD', 0.5, math('MULTIPLY', ao_small.outputs['AO'], 0.5)))
    shaded = N.new('ShaderNodeVectorMath')
    shaded.operation = 'SCALE'
    L.new(gold.outputs['Result'], shaded.inputs[0])
    L.new(occl, shaded.inputs['Scale'])
    L.new(shaded.outputs[0], emit.inputs['Color'])
    return m


# 2./3. Colour and roughness are evaluated on the low statue itself (its own AO), not projected from the high one:
# projection misses on thin claws and spikes streaked the first bake.
scene.render.bake.use_selected_to_active = False
scene.render.bake.margin = 16
for o in (fig,):
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
