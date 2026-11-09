"""Binding scale by side-silhouette area (flyer rule): the Standing clip's frame 0 rendered orthographic from its right
side (the native view-2 profile) as a mask; area in m^2 vs the native m394sa2 alpha area in px (frame scale 1.0).
scale = sqrt(native px / model m^2). Also prints the length- and height-based estimates. Args: -- <blend>"""
import bpy, sys, os, math
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[-1]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
act = bpy.data.actions['Standing']; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.frame_set(0)
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (1, 1, 1); sc.render.film_transparent = True
W, H, S = 1200, 600, 3.0
sc.render.resolution_x, sc.render.resolution_y = W, H
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); cam.data.type = 'ORTHO'; cam.data.ortho_scale = S
cam.location = (-6, 0, 0.35); cam.rotation_euler = (math.radians(90), 0, math.radians(-90)); sc.camera = cam
sc.render.filepath = os.path.join(HERE, 'work', 'sil_side.png'); bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(sc.render.filepath); px = np.array(img.pixels[:]).reshape(H, W, 4)[..., 3] > 0.5
area = px.sum() * (S / W) ** 2
ys, xs = np.nonzero(px); length = (xs.max() - xs.min() + 1) * S / W; height = (ys.max() - ys.min() + 1) * S / W
NAT_AREA, NAT_L, NAT_H = 7705, 225, 92          # native m394sa2 alpha: pixels, width, height (Blender has no PIL)
print(f'SCALE area {math.sqrt(NAT_AREA / area):.2f} length {NAT_L / length:.2f} height {NAT_H / height:.2f}'
      f' (model area {area:.3f} m2 length {length:.3f} height {height:.3f})')
