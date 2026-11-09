"""MM9 side of the comparison sheets: the true-handed MM9 GLB at clip times, front/back/quarter. Args: <glb> <out prefix> <view> <clip:seconds>..."""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene
for o in sc.objects:
    if o.name.startswith('Icosphere'): o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 520
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.21, 0.23); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 2.5; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
ds = {'front': (0, -1, 0.05), 'back': (0, 1, 0.05), 'quarter': (-0.7, -1, 0.1)}
d = Vector(ds[a[2]]).normalized(); cam.location = d * 10 + Vector((0, 0, 0.09)); cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
fps = sc.render.fps
for k, it in enumerate(a[3:]):
    c, t = it.split(':')
    act = bpy.data.actions[c]
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f = float(t) * fps
    sc.frame_set(int(f), subframe=f % 1.0)
    sc.render.filepath = f'{a[1]}_{a[2]}_{k}.png'; bpy.ops.render.render(write_still=True)
print('MM9 done')
