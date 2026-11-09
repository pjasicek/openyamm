"""Contact sheet of cobra clips: per clip n frames, three-quarter (top row) and top view (bottom row).
Args: -- out.png n Clip[,Clip...]"""
import bpy, sys, subprocess, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
out, n, acts = a[0], int(a[1]), a[2].split(',')
sc = bpy.context.scene; rig = bpy.data.objects['Hydra_Rig']
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.show_cavity = True; sh.color_type = 'SINGLE'; sh.single_color = (0.35, 0.45, 0.48)
sh.background_type = 'VIEWPORT'; sh.background_color = (0.75, 0.73, 0.68)
plane = bpy.data.objects.new('floor', bpy.data.meshes.new('floor')); sc.collection.objects.link(plane)
plane.data.from_pydata([(-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)], [], [(0, 1, 2, 3)])
sc.render.resolution_x, sc.render.resolution_y = 300, 300
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0
cells = []
for act in acts:
    A = bpy.data.actions[act]; rig.animation_data_create(); rig.animation_data.action = A
    f0, f1 = A.frame_range
    for k in range(n):
        f = f0 + (f1 - f0) * k / max(n - 1, 1); sc.frame_set(int(f))
        for v, (d, tgt) in enumerate((((0.5, 1, -0.3), (0.1, 0.3, 0.4)), ((-1, 0, -0.1), (0.1, 0.3, 0.4)))):
            d = Vector(d).normalized(); cam.location = Vector(tgt) - d * 6
            cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            p = f'/tmp/hyd_sheet_{act}_{k}_{v}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
            cells.append((act, k, f / 24.0, v, p))
code = """
import sys, json
from PIL import Image, ImageDraw
cells = json.loads(sys.argv[2]); n = int(sys.argv[3]); acts = sorted({c[0] for c in cells}, key=[c[0] for c in cells].index)
o = Image.new('RGB', (300 * n, 600 * len(acts))); d = ImageDraw.Draw(o)
for act, k, t, v, p in cells:
    r = acts.index(act); o.paste(Image.open(p), (k * 300, r * 600 + v * 300))
    if v == 0: d.text((k * 300 + 4, r * 600 + 4), f'{act} {t:.2f}s', fill=(120, 20, 20))
o.save(sys.argv[1])
"""
subprocess.run(['/usr/bin/python3', '-c', code, out, json.dumps(cells), str(n)], check=True)
print('SHEET', out)
