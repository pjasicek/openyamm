"""Attachment GLB of one hat: three LOD meshes in the head bone's own space (glTF), then hats/post_hat.py. Args (Blender):
<blend> <out glb> <head world 16 numbers json> <base png> [normal png] [orm png]"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
h = bpy.data.objects['Hat']
for o in list(bpy.data.objects):
    if o is not h: bpy.data.objects.remove(o)
LIFT, Wi = json.load(open(a[2]))['lift'], np.linalg.inv(np.array(json.load(open(a[2]))['head_world']))
me = h.data
co = np.array([tuple(h.matrix_world @ v.co) for v in me.vertices])
import os
sx, dz = (float(x) for x in os.environ.get('HAT_XFORM', '1 0').split())       # re-seat after the paint: scale about the brim centre, lift
cen = np.array([0, 0.5 * (co[:, 1].min() + co[:, 1].max()), co[:, 2].min()])
co = (co - cen) * sx + cen + np.array([0, 0, dz])
g = np.c_[co[:, 0], co[:, 2] + LIFT, -co[:, 1], np.ones(len(co))]      # master (z up) -> glTF world
loc = (Wi @ g.T).T[:, :3]
for v, p in zip(me.vertices, loc):
    v.co = Vector((p[0], -p[2], p[1]))                                 # back to Blender axes for the exporter's y-up conversion
h.matrix_world = __import__('mathutils').Matrix.Identity(4); h.parent = None
mat = bpy.data.materials.new('Hat'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(a[3]); nt.links.new(tx.outputs['Color'], bsdf.inputs['Base Color'])
if len(a) > 4:
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(a[4]); n.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    r = nt.nodes.new('ShaderNodeTexImage'); r.image = bpy.data.images.load(a[5]); r.image.colorspace_settings.name = 'Non-Color'
    sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(r.outputs['Color'], sp.inputs['Color']); nt.links.new(sp.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sp.outputs['Blue'], bsdf.inputs['Metallic'])
else:
    bsdf.inputs['Roughness'].default_value = 0.6
me.materials.clear(); me.materials.append(mat)
for p in me.polygons: p.use_smooth = True
objs = [h]
tris = len(me.polygons)
for k, r in enumerate((0.5, 0.2), 1):
    o = h.copy(); o.data = me.copy(); o.name = f'Hat_LOD{k}'; bpy.context.scene.collection.objects.link(o)
    for x in bpy.data.objects: x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    d = o.modifiers.new('D', 'DECIMATE'); d.ratio = r; d.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=d.name); objs.append(o)
for x in bpy.data.objects: x.select_set(x in objs)
bpy.ops.export_scene.gltf(filepath=a[1], use_selection=True, export_format='GLB', export_yup=True, export_animations=False, export_skins=False, export_attributes=False)
print('HATEXPORT', [len(o.data.polygons) for o in objs])
