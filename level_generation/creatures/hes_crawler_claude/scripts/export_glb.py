"""Export the crawler master (body material Crawler_A + the attachment materials, every clip) to
export/hes_crawler_lod0.glb. Args: -- [out.glb] [basecolor png] (defaults: export/hes_crawler_lod0.glb, the graded
shared base colour). Clips are exported at their own frame ranges (Walking/Running keyed at 60 fps, the rest at 30 fps:
the scene runs at 60 fps and the 30 fps actions are retimed x2 on export via their 'fps' property)."""
import bpy, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = os.path.join(HERE, a[0]) if a else os.path.join(HERE, 'export', 'hes_crawler_lod0.glb')
basecolor = os.path.join(HERE, a[1]) if len(a) > 1 else os.path.join(T, 'hcr_basecolor_graded.png')
keep = a[2].split(',') if len(a) > 2 and a[2] else None      # attachment materials to keep (viewer per tier)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
mesh = bpy.data.objects['Crawler']; rig = bpy.data.objects['Crawler_Rig']

mat = bpy.data.materials.get('Crawler_A') or bpy.data.materials.new('Crawler_A')
mat.use_nodes = True; nt = mat.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL' and n.type != 'BSDF_PRINCIPLED':
        nt.nodes.remove(n)
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(path, cs):
    img = bpy.data.images.load(path, check_existing=False); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


bc = tex(basecolor, 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex(os.path.join(T, 'hcr_normal_1k.png'), 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex(os.path.join(T, 'hcr_mr_1k.png'), 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials[0] = mat
if keep is not None:                                    # drop the attachment geometry this tier does not carry
    import bmesh
    names = [m.name for m in mesh.data.materials]
    drop = {i for i, n in enumerate(names) if i > 0 and n not in keep}
    bm = bmesh.new(); bm.from_mesh(mesh.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in drop], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(mesh.data); bm.free()
sc = bpy.context.scene
sc.render.fps = 60; sc.render.fps_base = 1
for act in bpy.data.actions:                            # 30 fps actions: stretch keys x2 into the 60 fps timeline
    if act.get('fps', 60) == 30 and not act.get('retimed'):
        for fc in getattr(act, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.co.x *= 2; kp.handle_left.x *= 2; kp.handle_right.x *= 2
        if not getattr(act, 'fcurves', None):
            for layer in act.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for fc in bag.fcurves:
                            for kp in fc.keyframe_points:
                                kp.co.x *= 2; kp.handle_left.x *= 2; kp.handle_right.x *= 2
        act.frame_start, act.frame_end = act.frame_start * 2, act.frame_end * 2
        act['retimed'] = True
rig.animation_data.action = bpy.data.actions['Standing']
if len(getattr(bpy.data.actions['Standing'], 'slots', [])):
    rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
sc.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True, export_def_bones=False)
print('EXPORTED', out)
