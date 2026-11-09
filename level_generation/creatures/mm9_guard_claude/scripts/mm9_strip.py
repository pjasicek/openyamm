"""Clip strip of a raw MM9 GLB (Blender diagnosis). Args: <glb> <out png> <clip,clip,...> [n per clip] [view q34|side|front]"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, clips = a[0], a[1], a[2].split(',')
n = int(a[3]) if len(a) > 3 else 6; view = a[4] if len(a) > 4 else 'q34'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene
for o in sc.objects:
    if o.name.startswith('Icosphere'):
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 260
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.5, 0.5)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 3.4; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
d = {'q34': Vector((1.0, -1.25, 0.25)), 'mir': Vector((-1.0, -1.25, 0.25)), 'side': Vector((1, 0, 0.05)), 'front': Vector((0, -1, 0.05))}[view].normalized()
cam.location = d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
fps = sc.render.fps
files = []
for c in clips:
    act = bpy.data.actions[c]
    rig.animation_data_create(); rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1)
        sc.frame_set(int(f), subframe=f - int(f))
        p = f'/tmp/claude-1000/strip_{c}_{i}.png'; sc.render.filepath = p
        bpy.ops.render.render(write_still=True); row.append(p)
    files.append((c, row))
open(out + '.list', 'w').write('\n'.join(c + '\t' + '\t'.join(r) for c, r in files))
