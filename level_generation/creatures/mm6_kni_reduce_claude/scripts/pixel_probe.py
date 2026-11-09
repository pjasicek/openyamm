"""Which surface a face_views.py 'hand' render shows at a pixel: casts the camera ray at Standing frame 0 and prints
the hit point. Usage: blender -b -P pixel_probe.py -- <glb> <x> <y> [size=600]"""
import bpy, sys
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
glb, px, py = args[0], float(args[1]), float(args[2]); size = float(args[3]) if len(args) > 3 else 600
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in list(bpy.data.objects):
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or o.name == 'Icosphere'):
        bpy.data.objects.remove(o)
act = bpy.data.actions['Standing']; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; sc.frame_set(0)
names = {b.name.lower().split(':')[-1].replace('b_', '').replace('_', ''): b for b in rig.pose.bones}
bone = lambda k: rig.matrix_world @ names[k].head
hand = bone('rhand'); fwd = bone('ltoe0') - bone('lfoot') + bone('rtoe0') - bone('rfoot'); fwd.z = 0; fwd.normalize()
side = Vector((-fwd.y, fwd.x, 0)); p = hand + fwd * .45 - side * .35 + Vector((0, 0, .15))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); cam.data.lens = 50
cam.location = p; cam.rotation_euler = (hand - p).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x = sc.render.resolution_y = int(size); bpy.context.view_layer.update()
fr = [cam.matrix_world @ v for v in cam.data.view_frame(scene=sc)]  # tr, br, bl, tl
u, v = px / size, py / size
top = fr[3].lerp(fr[0], u); bot = fr[2].lerp(fr[1], u); target = top.lerp(bot, v)
dg = bpy.context.evaluated_depsgraph_get()
hit, loc, nrm, idx, obj, _ = sc.ray_cast(dg, cam.location, (target - cam.location).normalized())
me = obj.data if obj else None
rest = tuple(round(c, 4) for c in me.polygons[idx].center) if obj else None
print('PIXEL', hit, 'rest', rest, obj.name if obj else None, tuple(round(c, 3) for c in loc), 'face', idx, 'normal', tuple(round(c, 2) for c in nrm))
