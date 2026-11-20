"""MM6 thief copy of mm6_gua_rebuild_claude/scripts/export_gua.py: Thief_A (body set, daggers in its top strip) and ThiefHead_A (head set).
Textured static export for clips_mm9.py: three materials (Guard body set, GuardHead head set, Halberd), head faces take HeadUV, smooth normals, the armature lifted so
model y = 0 is the floor. Tier A images; tier_materials.py adds B and C after the LODs. Args: <blend> <out glb>"""
import bpy, sys, os
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
TX = bpy.path.abspath('//../textures')
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for b in rig.pose.bones: b.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
nf = len(me.polygons)
hd = np.zeros(nf, np.int32); pl = np.zeros(nf, np.int32)
me.attributes['head'].data.foreach_get('value', hd)
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    if hd[p.index]:
        for li in p.loop_indices: buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
for n in [u.name for u in me.uv_layers if u.name != 'UVMap']:
    me.uv_layers.remove(me.uv_layers[n])


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
me.materials.append(material('Thief_A', 'thf_basecolor.png', 'thf_normal_1k.png', 'thf_metal_rough_1k.png'))
me.materials.append(material('ThiefHead_A', 'thf_head_basecolor.png', 'thf_head_normal_1k.png', 'thf_head_metal_rough_1k.png'))
me.polygons.foreach_set('material_index', (hd + 2 * pl).tolist())
for a in [a.name for a in me.attributes if a.name in ('head', 'hand', 'pole', 'lining', 'part', 'garm', 'srcp', 'graft_s', 'graft_side', 'weapon')]:
    me.attributes.remove(me.attributes[a])
for vg in [g.name for g in body.vertex_groups if g.name.startswith('MP_')]:
    body.vertex_groups.remove(body.vertex_groups[vg])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects: o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'Thief'; me.name = 'Thief'
for o in bpy.data.objects: o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', OUT, len(me.polygons))
