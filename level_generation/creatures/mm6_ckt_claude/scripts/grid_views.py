"""Orthographic top / side / front renders of the grounded raw mesh (stray piece removed) with a 5 cm world grid
drawn on top, for reading joint positions. Args: out_prefix"""
import bpy, sys, os, json, subprocess
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
m = next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([tuple(m.matrix_world @ v.co) for v in m.data.vertices]); zmin = co[:, 2].min()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.show_cavity = True; sh.show_xray = True; sh.xray_alpha = 0.55
sh.background_type = 'VIEWPORT'; sh.background_color = (0.9, 0.9, 0.9)
N = 1400; S = 1.1
sc.render.resolution_x = sc.render.resolution_y = N
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = S
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
views = {'top': ((0, 0.0, zmin + 0.2), (0, 0, 1), (1, 0, 0), (0, 1, 0)),      # centre, view dir(from), img x axis, img y axis
         'side': ((0, 0.0, zmin + 0.25), (-1, 0, 0), (0, -1, 0), (0, 0, 1)),
         'front': ((0, 0.0, zmin + 0.25), (0, -1, 0), (1, 0, 0), (0, 0, 1))}
meta = {}
for name, (c, d, ax, ay) in views.items():
    c = Vector(c); d = Vector(d)
    z = d.normalized(); x = Vector(ax); y = Vector(ay)
    cam.matrix_world = Matrix.Translation(c + d * 3) @ Matrix((x, y, z)).transposed().to_4x4()
    sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
    meta[name] = {'centre': list(c), 'ax': ax, 'ay': ay}
json.dump({'N': N, 'S': S, 'zmin': zmin, 'views': meta}, open(out + '_grid.json', 'w'))
subprocess.run(['/usr/bin/python3', '-c', """
import json, sys
from PIL import Image, ImageDraw
out = sys.argv[1]; g = json.load(open(out + '_grid.json')); N, S = g['N'], g['S']
for name, v in g['views'].items():
    im = Image.open(f'{out}_{name}.png').convert('RGB'); d = ImageDraw.Draw(im)
    c = v['centre']; ax, ay = v['ax'], v['ay']
    cx = sum(a * b for a, b in zip(c, ax)); cy = sum(a * b for a, b in zip(c, ay))
    for k in range(-12, 13):
        val = k * 0.05
        px = (val - cx) / S * N + N / 2; py = N / 2 - (val - cy) / S * N
        col = (255, 0, 0) if k % 2 == 0 else (255, 170, 170)
        d.line([(px, 0), (px, N)], fill=col, width=1); d.line([(0, py), (N, py)], fill=col, width=1)
        if k % 2 == 0:
            d.text((px + 2, 2), f'{val:+.1f}', fill=(200, 0, 0)); d.text((2, py + 2), f'{val:+.1f}', fill=(200, 0, 0))
    im.save(f'{out}_{name}.png')
""", out], check=True)
print('GRID', zmin)
