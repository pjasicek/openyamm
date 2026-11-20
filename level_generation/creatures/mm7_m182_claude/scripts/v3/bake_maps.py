"""Per-texel maps of the v3 runtime UV layout (Blender, Cycles bakes on work/v3/uv_master.blend, rest pose), per
texture set (body / head / wings, 2048): rest position, smooth normal, part attributes (R = v3part / 4 + head piece class, G = wing membrane face flag or neck patch (scripts/v3/reshape_neck.py), G = membrane
face flag, B = coverage) with no margin, and short-range AO (reach 0.04 m, 2048, margin 8).
Membrane faces: scripts/v3/wing_classes.py (farther than 5.5 cm from the wing bone chain).
Out: work/v3/bake/{set}_{pos,nrm,attr}.npy (float32, row 0 = top), work/v3/bake/{set}_ao.png"""
import bpy, numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[2]; OUT = P / 'work/v3/bake'; OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
o = bpy.data.objects['Body']; me = o.data; rig = bpy.data.objects['Rig']
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()

o.modifiers.clear(); o.parent = None
me.uv_layers.active = me.uv_layers['UVMap']
for l in me.uv_layers: l.active_render = (l.name == 'UVMap')
import sys; sys.path.insert(0, str(P / 'scripts/v3')); import wing_classes
wing_classes.classify(o, rig)          # face attribute 'membrane': wing faces off the wing bone chain
partf = me.attributes.new('partf', 'FLOAT', 'POINT')      # v3part / 4 + hpiece (head piece class 0..3)
hp = me.attributes['hpiece'].data
pf = P / 'work/v3b/neck_patch.npy'; patch = np.load(pf) if pf.exists() else np.zeros(len(me.vertices), bool)
for i, d in enumerate(me.attributes['v3part'].data): partf.data[i].value = d.value / 4 + hp[i].value
# neck patch flag in its own channel (G, with the wing membrane flag: they never share a face); adding it to the
# part code made faces on the patch border interpolate to false classes (a white 'horn' line in v3b's first bake)
pa = me.attributes.new('patchf', 'FLOAT', 'POINT')
for i in range(len(me.vertices)): pa.data[i].value = float(patch[i])
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
sc.world = sc.world or bpy.data.worlds.new('w')
N = 2048
images = {}
slots = [p.material_index for p in me.polygons]
mats = []
for k, label in enumerate(['body', 'head', 'wings']):
    m = bpy.data.materials.new('B_' + label); m.use_nodes = True; mats.append(m)
me.materials.clear()
for m in mats: me.materials.append(m)
for p in me.polygons: p.material_index = slots[p.index]
for o2 in bpy.data.objects: o2.select_set(o2 == o)
bpy.context.view_layer.objects.active = o


def setup(kind, label, m):
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], out.inputs[0])
    if kind == 'pos':
        g = nt.nodes.new('ShaderNodeNewGeometry'); nt.links.new(g.outputs['Position'], em.inputs['Color'])
    elif kind == 'nrm':
        g = nt.nodes.new('ShaderNodeNewGeometry'); nt.links.new(g.outputs['Normal'], em.inputs['Color'])
    elif kind == 'attr':
        a1 = nt.nodes.new('ShaderNodeAttribute'); a1.attribute_name = 'partf'
        a2 = nt.nodes.new('ShaderNodeAttribute'); a2.attribute_name = 'membrane'; a2.attribute_type = 'GEOMETRY'
        a3 = nt.nodes.new('ShaderNodeAttribute'); a3.attribute_name = 'patchf'
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; nt.links.new(a2.outputs['Fac'], mx.inputs[0]); nt.links.new(a3.outputs['Fac'], mx.inputs[1])
        cc = nt.nodes.new('ShaderNodeCombineColor'); cc.inputs[2].default_value = 1.0
        nt.links.new(a1.outputs['Fac'], cc.inputs[0]); nt.links.new(mx.outputs[0], cc.inputs[1]); nt.links.new(cc.outputs[0], em.inputs['Color'])
    else:   # AO: plain diffuse
        nt.nodes.remove(em); bs = nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(bs.outputs[0], out.inputs[0])
    key = f'{label}_{kind}'
    img = bpy.data.images.new(key, N, N, alpha=True, float_buffer=(kind != 'ao'))
    img.generated_color = (0, 0, 0, 0)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.nodes.active = t; images[key] = img
for kind in ['pos', 'nrm', 'attr', 'ao']:
    for m, label in zip(mats, ['body', 'head', 'wings']): setup(kind, label, m)
    if kind == 'ao':
        sc.cycles.samples = 64; sc.world.light_settings.distance = 0.04; sc.render.bake.margin = 8
        bpy.ops.object.bake(type='AO')
    else:
        sc.cycles.samples = 1; sc.render.bake.margin = 0
        bpy.ops.object.bake(type='EMIT')
    for label in ['body', 'head', 'wings']:
        img = images[f'{label}_{kind}']
        if kind == 'ao':
            img.filepath_raw = str(OUT / f'{label}_ao.png'); img.file_format = 'PNG'; img.save()
        else:
            a = np.array(img.pixels[:], np.float32).reshape(N, N, 4)[::-1]
            np.save(OUT / f'{label}_{kind}.npy', a)
    print('BAKED', kind, flush=True)
