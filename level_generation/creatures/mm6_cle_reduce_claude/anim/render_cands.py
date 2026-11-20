"""Frames of cleric clips (mesh + staff, workbench, textured) for candidate sheets: one row per action, <n> frames,
camera from the party's side (front) or three-quarter. Writes <out dir>/frames.json for compose_sheet.py.
Args: -- <blend> <out dir> <view front|q34|side> <n> <Action> [...]"""
import bpy, sys, os, json, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, view, n, acts = a[0], a[1], a[2], int(a[3]), a[4:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; rig = bpy.data.objects['Cleric_Rig']
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 300, 380
sc.render.film_transparent = False
cam = bpy.data.objects.new('CandCam', bpy.data.cameras.new('CandCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get("CAND_SCALE", 2.3))
yaw = {'front': 0.0, 'q34': 40.0, 'side': 90.0}[view]
d = Vector((math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)), 0.12)).normalized()
c = Vector((0, -0.2, 0.9)); cam.location = c + d * 6
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
rows = []
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1)
        sc.frame_set(int(f), subframe=f - int(f))
        p = os.path.join(out, f'{name}_{i}.png'); sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        row.append([p, f'{name} {f / sc.render.fps:.2f}s'])
    rows.append(row)
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'))
print('RENDERED', len(rows))
