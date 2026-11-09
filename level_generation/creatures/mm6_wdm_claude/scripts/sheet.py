"""Contact sheet of actions on the demon (front + side). Args: blend-loaded; -- out.png n action[,action...]."""
import bpy, sys, math, subprocess
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
out, n, acts = a[0], int(a[1]), a[2].split(',')
sc = bpy.context.scene; rig = bpy.data.objects['Demon_Rig']
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.show_cavity = True; sh.color_type = 'SINGLE'; sh.single_color = (0.62, 0.45, 0.62)
sh.background_type = 'VIEWPORT'; sh.background_color = (0.25, 0.27, 0.3)
sc.render.resolution_x, sc.render.resolution_y = 300, 300
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.4
cells = []
for act in acts:
    A = bpy.data.actions[act]; rig.animation_data_create(); rig.animation_data.action = A
    f0, f1 = A.frame_range
    for k in range(n):
        f = f0 + (f1 - f0) * k / (n - 1)
        sc.frame_set(int(f), subframe=f - int(f))
        for d in ((0, 1, 0.05), (-1, 0, 0.05)):
            d = Vector(d).normalized(); cam.location = Vector((0, 0, 1.1)) - d * 6
            cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            p = f'/tmp/wdm_sheet_{act}_{k}_{len(cells)}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
            cells.append((act, k, f / 24.0, p))
code = """
import sys, json
from PIL import Image, ImageDraw
cells = json.loads(sys.argv[2]); n = int(sys.argv[3]); rows = len(cells) // (2 * n)
o = Image.new('RGB', (300 * n, 600 * rows)); d = ImageDraw.Draw(o)
for i, (act, k, t, p) in enumerate(cells):
    r = i // (2 * n); c = (i % (2 * n)) // 2; v = i % 2
    o.paste(Image.open(p), (c * 300, r * 600 + v * 300))
    if v == 0: d.text((c * 300 + 4, r * 600 + 4), f'{act} {t:.2f}s', fill=(255, 220, 120))
o.save(sys.argv[1])
"""
import json
subprocess.run(['/usr/bin/python3', '-c', code, out, json.dumps(cells), str(n)], check=True)
print('SHEET', out)
