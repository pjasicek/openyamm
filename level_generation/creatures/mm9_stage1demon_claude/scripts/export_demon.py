"""Textured static export for clips_mm9.py (from mm9_ghoul_claude/scripts/export_ghoul.py): materials LesserDemon (body set) and LesserDemonHead (head set); head faces take HeadUV;
the armature lifted so model y = 0 is the floor. Args: <uv blend> <out glb> <body base> <head base> <normal> <orm> <head normal> <head orm>"""
import bpy, bmesh, sys, os
import numpy as np
A = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, BASE, HBASE, NORM, ORM, HNORM, HORM = A
bpy.ops.wm.open_mainfile(filepath=IN)
TX = bpy.path.abspath('//../textures')
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for b in rig.pose.bones: b.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
nf_ = len(me.polygons)
hd = np.zeros(nf_, np.int32); me.attributes['head'].data.foreach_get('value', hd)
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    if hd[p.index]:
        for li in p.loop_indices: buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(TX, fname), check_existing=True); img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


me.materials.clear()
me.materials.append(material('LesserDemon', BASE, NORM, ORM))
me.materials.append(material('LesserDemonHead', HBASE, HNORM, HORM))
me.polygons.foreach_set('material_index', hd.tolist())
for a in [a.name for a in me.attributes if a.name in ('head', 'part', 'digit', 'drop', 'oldhead')]:
    me.attributes.remove(me.attributes[a])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects: o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = float(os.environ.get('LIFT', -min((body.matrix_world @ v.co).z for v in me.vertices)))
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'LesserDemon'; me.name = 'LesserDemon'
for o in bpy.data.objects: o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', OUT, len(me.polygons))
