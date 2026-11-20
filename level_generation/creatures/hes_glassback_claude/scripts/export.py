"""Runtime export: work/anim_v2.blend (reduced LOD0 mesh, clips) -> export/hes_glassback_lod0.glb.
One skinned mesh 'Glassback': materials Glassback_A (body 1K set, UVMap) and GlassbackHead_A (head 1K set; HeadUV
written into TEXCOORD_0 for the head faces). Socket bone Socket_Beak (non-deforming, on Head, at the beak tip: the
attack's contact point). The crest is not part of it (crest_export.py: rigid attachments per bone). Clips at 24 fps,
quaternions sign-continuous (anim.py). Args: -- <blend> <out.glb>"""
import bpy, os, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
T = C.path('textures')
bpy.ops.wm.open_mainfile(filepath=C.path(src))
sc = bpy.context.scene; sc.render.fps = 24; sc.render.fps_base = 1
for o in list(bpy.data.objects):
    if o.name.startswith('Crest') or o.name == 'Floor':
        bpy.data.objects.remove(o, do_unlink=True)
rig = bpy.data.objects[C.RIG]; body = bpy.data.objects[C.MESH]; me = body.data
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    if hd[p.index]:
        for li in p.loop_indices:
            buv[li].uv = huv[li].uv
me.uv_layers.remove(me.uv_layers['HeadUV'])
# beak socket
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
tip = Vector((0, -1.44, 0.60))
s = eb.new('Socket_Beak'); s.head = tip; s.tail = tip + Vector((0, -0.05, 0)); s.parent = eb['Head']; s.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    def tex(f, cs):
        img = bpy.data.images.load(os.path.join(T, f)); img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    bc = tex(base, 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
    nm = tex(normal, 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    m = tex(mr, 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(m.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


me.materials.clear()
me.materials.append(material('Glassback_A', 'hgb_basecolor_1k_graded.png', 'hgb_normal_1k.png', 'hgb_metal_rough_1k.png'))
me.materials.append(material('GlassbackHead_A', 'hgb_head_basecolor_1k_graded.png', 'hgb_head_normal_1k.png',
                             'hgb_head_metal_rough_1k.png'))
for p in me.polygons:
    p.material_index = int(hd[p.index])
me.attributes.remove(me.attributes['head'])
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(1)
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=C.path(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out, 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
