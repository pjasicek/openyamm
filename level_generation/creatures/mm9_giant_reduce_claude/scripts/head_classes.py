"""Hair faces of the head set for the relaxed prio-1 cut (brief: hair shells 0.6-0.8, the face skin and neck seam exact).
Rest pose, mesh-local (z up, face towards -y). A head-set face is hair when it lies
- above the hairline (z > ZH) and behind the brow line (y > YBROW), or
- behind the ears (y > YEAR), or
- on a side lock (|x| > XLOCK and y > YLOCK and z > ZLOCK),
and not within one face ring of the neck seam (the head set's border with the body) or of the eyes. Everything else (face
skin, brows, eyes, nose, mouth, beard on the jaw, ears, neck) stays exact. Writes work/head_hair.npy and renders the
classes (blue hair, orange kept) from five views into review/head_classes/. Usage: blender -b -P head_classes.py"""
import os
import bpy
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda k, d: float(os.environ.get(k, d))
ZH, YBROW, YEAR, XLOCK, YLOCK, ZLOCK = E('ZH', '1.16'), E('YBROW', '-0.21'), E('YEAR', '-0.04'), E('XLOCK', '0.125'), E('YLOCK', '-0.16'), E('ZLOCK', '0.98')
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); F, V = d['faces'], d['verts']
mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int); head = mat == 1
cen = V[F].mean(1); x, y, z = cen[:, 0], cen[:, 1], cen[:, 2]
hair = head & (((z > ZH) & (y > YBROW)) | (y > YEAR) | ((np.abs(x) > XLOCK) & (y > YLOCK) & (z > ZLOCK)))
# seam ring: head faces sharing a vertex with a body face, and the ring next to them; the eyes (small pieces) and a ring
bodyv = np.zeros(len(V), bool); bodyv[F[~head].ravel()] = True
seam = head & bodyv[F].any(1)
sv = np.zeros(len(V), bool); sv[F[seam].ravel()] = True; seam |= head & sv[F].any(1)
eyes = head & (np.abs(y + 0.18) < 0.05) & (np.abs(z - 1.098) < 0.04) & (np.abs(np.abs(x) - 0.041) < 0.04)
hair &= ~seam & ~eyes
np.save(os.path.join(HERE, 'work', 'head_hair.npy'), hair)
print('HAIR', int(hair.sum()), 'of', int(head.sum()), 'head faces; seam', int(seam.sum()))
# render
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
me = bpy.data.meshes.new('h'); hf = np.where(head)[0]
me.from_pydata([tuple(p) for p in V.tolist()], [], [tuple(F[i]) for i in hf]); me.update()
mats = [bpy.data.materials.new('keep'), bpy.data.materials.new('hair')]
mats[0].diffuse_color = (1, .55, .2, 1); mats[1].diffuse_color = (.2, .45, 1, 1)
for m in mats:
    me.materials.append(m)
for p, i in zip(me.polygons, hf):
    p.material_index = int(hair[i])
o = bpy.data.objects.new('h', me); sc.collection.objects.link(o)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.5
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 400
c = Vector((0, -0.05, 1.08)); out = os.path.join(HERE, 'review', 'head_classes'); os.makedirs(out, exist_ok=True)
for name, dv in (('front', (0, -1, .05)), ('q34', (-.7, -.7, .15)), ('side', (-1, 0, .05)), ('back', (0, 1, .1)), ('top', (0, -.3, 1))):
    cam.location = c + Vector(dv).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png'); bpy.ops.render.render(write_still=True)
print('RENDERED')
