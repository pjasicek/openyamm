"""Ram export: RAM.abc is SHEEP.abc's body, ears, tail and skeleton (identical vertices, UVs and bind) plus a `ramhorn`
piece rigid on Xheadpiv, and it plays SHEEP.abc's clips (its only own clip is the setup pose). So the ram reuses the
sheep's animated master (mesh, weights, UVs, textures, role clips) and adds the procedural horns (horn_geom.py).

Args: <sheep anim blend> <out blend> <out glb> <lift>
The body material is renamed 'Ram' (tier ram_a: SHEEP2.dtx ramps on the shared sheep textures); the horns join the
body mesh as material 'RamHorn' (own 1K maps from compose_horn.py, RAMHORNBLACK.dtx colours).
"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import horn_geom as H

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, LIFT = argv[0], argv[1], argv[2], float(argv[3])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig)
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
rig.name = 'Ram_Rig'
body.name = 'Ram'
body.data.name = 'Ram'
body.data.materials[0].name = 'Ram'

# horns as a second material of the body mesh, rigid on Xheadpiv
mat = bpy.data.materials.new('RamHorn')
mat.use_nodes = True
mat.use_backface_culling = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(name, cs):
    img = bpy.data.images.load(os.path.join(TEX, name))
    img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = img
    return n


nt.links.new(tex('ramhorn_basecolor.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tex('ramhorn_normal_1k.png', 'Non-Color').outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(tex('ramhorn_metal_rough_1k.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
body.data.materials.append(mat)
slot = len(body.data.materials) - 1

me = body.data
bm = bmesh.new(); bm.from_mesh(me)
uvl = bm.loops.layers.uv.active
dl = bm.verts.layers.deform.active
gi = body.vertex_groups['Xheadpiv'].index if 'Xheadpiv' in body.vertex_groups else body.vertex_groups.new(name='Xheadpiv').index
inv = body.matrix_world.inverted()
info = {}
for side in (-1, 1):
    V, T, UV, info = H.build(side)
    V = V + np.array([0, 0, LIFT])
    vs = []
    for p in V:
        v = bm.verts.new(tuple(inv @ __import__('mathutils').Vector(tuple(p))))
        v[dl][gi] = 1.0
        vs.append(v)
    for tri, uvs in zip(T, UV):
        f = bm.faces.new([vs[k] for k in tri])
        f.material_index = slot
        f.smooth = True
        for loop, uv in zip(f.loops, uvs):
            loop[uvl].uv = tuple(uv)
bm.to_mesh(me); bm.free()
horn_tris = sum(1 for p in me.polygons if p.material_index == slot)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('RAM_EXPORT ' + json.dumps({'tris': len(me.polygons), 'horn_tris': horn_tris, 'horn_layout': info}, default=float))
