"""Contact sheet of clips on the natf master (body, blade and shield): one row per action, N frames evenly over the
clip, workbench with textures, fixed camera. Usage: blender -b -P clip_sheet.py -- <blend> <out.png> <view> <N> <action> [...]
view: q34 (three-quarter front from her right), front, right."""
import os, sys, math, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, view, N, acts = a[0], a[1], a[2], int(a[3]), a[4:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x = sc.render.resolution_y = 400; sc.render.film_transparent = False
sc.world.color = (.42, .43, .45) if sc.world else None
cam = bpy.data.objects.new('SheetCam', bpy.data.cameras.new('SheetCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0
d = {'q34': (-.75, -1, .25), 'front': (0, -1, .15), 'right': (-1, 0, .15)}[view]  # she faces -Y, her right is -X
c = Vector((0, 0, .95)); dv = Vector(d).normalized(); cam.location = c + dv * 6
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
tmp = os.path.abspath(out) + '_tiles'; os.makedirs(tmp, exist_ok=True)
rows = []
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    row = []
    for k in range(N):
        f = f0 + (f1 - f0) * k / (N - 1); sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        p = os.path.join(tmp, f'{an}_{k}.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True); row.append(p)
    rows.append((an, row, f1 - f0))
import json
json.dump([[an, row, dur] for an, row, dur in rows], open(out + '.json', 'w'))
