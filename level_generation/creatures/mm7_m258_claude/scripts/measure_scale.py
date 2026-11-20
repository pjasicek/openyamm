"""Binding scale for a flyer by silhouette area (quadruped playbook, flyers): mean front-view alpha area of the Fly
clip (7 evenly spaced frames, orthographic, m^2) against the native front fly frames m258w[a-g]0 (alpha px^2 x
frame scale 1.299988^2 = game units^2). Prints scale = sqrt(native / model). Args: -- <blend>"""
import bpy, sys, os, math
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.film_transparent = True
RES, OS_ = 600, 5.0
sc.render.resolution_x = sc.render.resolution_y = RES
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = OS_
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -10, 1.3); cam.rotation_euler = (math.radians(90), 0, 0)
A = bpy.data.actions['Fly']; rig.animation_data_create(); rig.animation_data.action = A
if len(A.slots): rig.animation_data.action_slot = A.slots[0]
f0, f1 = A.frame_range; areas = []
out = os.path.join(HERE, 'work', '_sil.png')
for k in range(7):
    sc.frame_set(int(f0 + (f1 - f0) * k / 7)); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(out); px = np.array(img.pixels[:]).reshape(-1, 4)
    areas.append(float((px[:, 3] > 0.5).sum()) * (OS_ / RES) ** 2); bpy.data.images.remove(img)
os.remove(out)
nat = []
for c in 'abcdefg':
    img = bpy.data.images.load(os.path.join(HERE, '..', 'mm7_m258', 'native', f'm258w{c}0.png'))
    a = np.array(img.pixels[:]).reshape(-1, 4)[:, 3]; bpy.data.images.remove(img)
    nat.append(float((a > 0.5).sum()) * 1.299988 ** 2)
m, n = np.mean(areas), np.mean(nat)
print(f'SCALE model front area m2 {m:.3f} (frames {np.round(areas, 3).tolist()}), native units2 {n:.0f}, scale {math.sqrt(n / m):.2f}')
