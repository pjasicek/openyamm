"""Right-hand close-ups rendered from an exported GLB (what the review viewer and the game load), Standing frame 0:
front, outer and inner, Workbench texture colour. Args: -- <glb> <out prefix> [action] [frame]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out = a[0], a[1]; action = a[2] if len(a) > 2 else 'Standing'; frame = int(a[3]) if len(a) > 3 else 0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
act = next(x for x in bpy.data.actions if x.name.split('|')[0] == action or x.name == action)
rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; sc.frame_set(int(act.frame_range[0]) + frame)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.3, 0.32, 0.35)
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.4
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
pb = next(b for b in rig.pose.bones if b.name.endswith('B_R_Hand'))
c = rig.matrix_world @ pb.head
# glTF import: the character faces -Y as authored (export_yup round trip)
for view, d, near in (('front', Vector((0, -1, 0)), 2.0), ('outer', Vector((-1, 0, 0)), 2.0), ('inner', Vector((1, 0, 0)), 0.2)):
    cam.location = c + d * near; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cd.clip_start = 0.01 if near > 1 else 0.05
    sc.render.filepath = f'{out}_{view}.png'; bpy.ops.render.render(write_still=True)
print('GLBHAND', action, 'hand head', [round(x, 3) for x in c], 'meshes', [o.name for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render])
