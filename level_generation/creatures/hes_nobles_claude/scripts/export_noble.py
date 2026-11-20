"""Runtime export of an assembly (work/assembly_<name>.blend) -> export/<out>_lod0.glb: one skinned mesh 'NOBLE' (the
winged body without the skin hidden under the carapace, the carapace shell NB_Plate / NB_Glow, the weapons 100 % on
their sockets, split out later by split_attachments.py), the set's clips at 48 fps. Body materials renamed NB_Body /
NB_Head (their textures kept). Also writes the body's base colour images to textures/ for the tier ramps.
Args: -- <assembly name> <out>"""
import bpy, sys, os, json
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
name, out = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work', f'assembly_{name}.blend'))
scene = bpy.context.scene; scene.render.fps = 48; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
for m, new in (('OV_Body_A', 'NB_Body'), ('OV_Head_A', 'NB_Head')):
    mat = bpy.data.materials.get(m)
    if mat: mat.name = new
for mat in (bpy.data.materials['NB_Body'], bpy.data.materials['NB_Head']):
    tex = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and any(l.to_socket.name == 'Base Color' for l in n.outputs[0].links))
    im = tex.image; path = os.path.join(P, 'textures', f'{mat.name.lower()}_basecolor_source.png')
    if not os.path.exists(path):
        im.filepath_raw = path; im.file_format = 'PNG'; im.save()
# the skin under the carapace
me = body.data
hid = np.array([x.value for x in me.attributes['shell_hidden'].data]) if 'shell_hidden' in me.attributes else np.zeros(len(me.vertices))
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
gone = [f for f in bm.faces if all(hid[v.index] for v in f.verts)]
bmesh.ops.delete(bm, geom=gone, context='FACES'); bm.to_mesh(me); bm.free()
for at in [x.name for x in me.attributes if x.name in ('piece', 'ivory', 'shell_hidden')]:
    me.attributes.remove(me.attributes[at])
parts = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and o is not body]
bpy.ops.object.select_all(action='DESELECT')
for o in parts + [body]: o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = body.data.name = 'NOBLE'
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o is not body]:
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True)
for act in bpy.data.actions:
    act.use_fake_user = True
for m in bpy.data.materials:                         # the wing membranes are double-sided; the shadow merge needs one culling
    m.use_backface_culling = False
os.makedirs(os.path.join(P, 'export'), exist_ok=True)
path = os.path.join(P, 'export', f'{out}_lod0.glb')
bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
info = {'glb': path, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'tris_by_material': {m.name: sum(len(p.vertices) - 2 for p in body.data.polygons if p.material_index == i)
                             for i, m in enumerate(body.data.materials)},
        'clips': {x.name: [int(v) for v in x.frame_range] for x in bpy.data.actions}}
json.dump(info, open(os.path.join(P, 'export', f'export_info_{out}.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info)); sys.stdout.flush(); os._exit(0)
