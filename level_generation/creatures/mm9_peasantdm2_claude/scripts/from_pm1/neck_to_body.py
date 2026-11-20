"""Neck flange back to the body set (2026-11-01, viewer shots): head_split.py's level cut (z 0.62, within 22 cm of the
neck) took the top of the shirt shell around the neck into the head set; the head retexture painted that flange
collar/skin colour, so flat patches showed inside the jacket collar. Head faces whose centroid lies below Z_MAX and
more than R_MIN from the neck axis go back to the body set (face attribute head = 0): their body-UV texels were
painted by the body retexture (the texture-pass upload carried every face, head ones at 0.35x density), so no new
paint is needed. Geometry, UVs and weights are unchanged.
Args (Blender): <in blend> <out blend> [z_max 0.66] [r_min 0.07]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
ZMAX = float(a[2]) if len(a) > 2 else 0.66
RMIN = float(a[3]) if len(a) > 3 else 0.07
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
nk = rig.matrix_world @ rig.data.bones['Bip01 Neck'].head_local
me = body.data
hd = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32)
me.attributes['hand'].data.foreach_get('value', hn)
moved = 0
for p in me.polygons:
    if not hd[p.index] or hn[p.index]:
        continue
    c = p.center
    if c.z < ZMAX and np.hypot(c.x - nk.x, c.y - nk.y) > RMIN:
        hd[p.index] = 0
        moved += 1
me.attributes['head'].data.foreach_set('value', hd.tolist())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('NECK2BODY', json.dumps({'faces_to_body': moved, 'z_max': ZMAX, 'r_min': RMIN, 'neck': list(nk)}))
