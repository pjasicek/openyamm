"""Close-up variant (PF3, 2026-11-02): views centred on the posed bone BONE (default FHP Neck) lowered by DROP m, ORTHO default 0.8.
Clay frames of a GLB: rows clip:seconds, columns views. Args: <glb> <out png> <items> [views]"""
import bpy, sys, math, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, items = a[0], a[1], a[2].split(',')
views = (a[3] if len(a) > 3 else 'front,side,q34').split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE' if not os.environ.get('TEX') else 'TEXTURE'
sh.single_color = (.72, .7, .62); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('SIZE', 420))
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.22, 0.26)
sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.ortho_scale = float(os.environ.get('ORTHO', 0.8)); cd.clip_end = 30
tiles = []
rows = []
for it in items:
    clip, t = it.split(':')
    act = bpy.data.actions[clip] if clip in bpy.data.actions else next(x for x in bpy.data.actions if x.name.startswith(clip))
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    fr = float(t) * 24.0
    sc.frame_set(int(fr), subframe=fr % 1.0)
    bpy.context.view_layer.update()
    P = np.array([tuple(rig.matrix_world @ b.head) for b in rig.pose.bones])
    pb = rig.pose.bones[os.environ.get('BONE', 'FHP Neck')]; c = np.array(rig.matrix_world @ pb.head); c[2] -= float(os.environ.get('DROP', 0.08))
    row = []
    for v in views:
        ang = {'front': 0, 'side': 90, 'q34': -38, 'back': 180, 'rside': -90, 'q34b': 145}[v]
        r = math.radians(ang); tgt = Vector(c)
        cam.location = tgt + Vector((math.sin(r) * 6, -math.cos(r) * 6, float(os.environ.get('UP', 0.7))))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        fn = f'{out}.{len(rows)}_{len(row)}.png'
        sc.render.filepath = fn; bpy.ops.render.render(write_still=True); row.append(fn)
    rows.append((it, row))
open(out + '.list', 'w').write('\n'.join(i + '\t' + '\t'.join(r) for i, r in rows))
print('FRAMES', out, len(rows))
