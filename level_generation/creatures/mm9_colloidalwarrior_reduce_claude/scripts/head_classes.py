"""Hood faces of the Colloidal Warrior's head set for the relaxed prio-1 cut (brief: hood shells 0.6-0.8; the face skin
and the neck seam exact). The head set is one dome over the hunched trunk: face in front (crest ridges, brows, eyes,
nose, grin, chin and throat rolls), the hood behind and above it. Rest pose, mesh-local (z up, face towards -y).
A head-set face is hood when its centroid lies behind the face plane (y > YFACE) or on the top behind the crest
(z > ZTOP and y > YTOP); never when it is on the head/body rim (region mask A, the neck seam) or within RING face rings
of it, or within RING rings of the face. Writes work/head_hood.npy and renders the classes (blue hood, orange kept) from
five views into review/head_classes/. Usage: blender -b -P head_classes.py"""
import os
import bpy
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda k, d: float(os.environ.get(k, d))
YFACE, ZTOP, YTOP, RING, SRING = E('YFACE', '-0.24'), E('ZTOP', '1.5'), E('YTOP', '0'), int(E('RING', '1')), int(E('SRING', '2'))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); F, V = d['faces'], d['verts']
wuv = d['wuv'].reshape(-1, 3, 2); mat = (wuv[:, 0, 0] // 2).astype(int); head = mat == 1
cen = V[F].mean(1); x, y, z = cen[:, 0], cen[:, 1], cen[:, 2]
hood = head & ((y > YFACE) | ((z > ZTOP) & (y > YTOP)))
# the region mask's A band (head_mask.py) is a painted colour blend 5-15 cm wide, not the seam: with RIM_MASK=1 it is
# kept whole; by default only the seam itself (head faces touching a body face) and RING rings round it are kept
rim = head & (np.load(os.path.join(HERE, 'work', 'head_mask.npy'))[:, 3] > 40) if E('RIM_MASK', '0') else np.zeros(len(F), bool)
bodyv = np.zeros(len(V), bool); bodyv[F[~head].ravel()] = True
rim |= head & bodyv[F].any(1)
face = head & ~hood
for _ in range(SRING):
    sv = np.zeros(len(V), bool); sv[F[rim].ravel()] = True; rim |= head & sv[F].any(1)
for _ in range(RING):
    sv = np.zeros(len(V), bool); sv[F[face].ravel()] = True; face |= head & sv[F].any(1)
hood &= ~rim & ~face
np.save(os.path.join(HERE, 'work', 'head_hood.npy'), hood)
print('HOOD', int(hood.sum()), 'of', int(head.sum()), 'head faces; rim', int(rim.sum()), 'face', int((head & ~hood & ~rim).sum()))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
me = bpy.data.meshes.new('h'); hf = np.where(head)[0]
me.from_pydata([tuple(p) for p in V.tolist()], [], [tuple(F[i]) for i in hf]); me.update()
mats = [bpy.data.materials.new('keep'), bpy.data.materials.new('hood'), bpy.data.materials.new('rim')]
mats[0].diffuse_color = (1, .55, .2, 1); mats[1].diffuse_color = (.2, .45, 1, 1); mats[2].diffuse_color = (.3, .9, .3, 1)
for mm in mats:
    me.materials.append(mm)
for p, i in zip(me.polygons, hf):
    p.material_index = 1 if hood[i] else (2 if rim[i] else 0)
o = bpy.data.objects.new('h', me); sc.collection.objects.link(o)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.0
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 400
c = Vector((0, -0.1, 0.71)); out = os.path.join(HERE, 'review', 'head_classes'); os.makedirs(out, exist_ok=True)
for name, dv in (('front', (0, -1, .05)), ('q34', (-.7, -.7, .15)), ('side', (-1, 0, .05)), ('back', (0, 1, .1)), ('top', (0, -.3, 1))):
    cam.location = c + Vector(dv).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png'); bpy.ops.render.render(write_still=True)
print('RENDERED')
