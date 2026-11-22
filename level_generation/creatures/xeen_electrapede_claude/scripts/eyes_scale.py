"""Shrink the two compound-eye ellipsoids (mesh part 2) of work/anim_base.blend and work/anim_v1.blend to 0.8 of their
size about their own centres, moved 0.8 cm forward along their facing so they still bulge from the head: the native
eyes are each about a quarter of the head's width (7-8 of 30 px), the first build's half. Vertex positions only: the
UV layout and the paint stay valid, the eyes stay rigid on Head. Idempotent (records the scale on the mesh)."""
import bpy, os
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S, FWD = 0.8, 0.008
for name in ('anim_base.blend', 'anim_v1.blend'):
    path = os.path.join(HERE, 'work', name)
    bpy.ops.wm.open_mainfile(filepath=path)
    ob = bpy.data.objects['Pede']; me = ob.data
    if me.get('eye_scale') == S:
        print('EYES already scaled', name); continue
    part = np.zeros(len(me.vertices), int)
    for p in me.polygons:
        for v in p.vertices:
            part[v] = me.attributes['part'].data[p.index].value
    for sd in (1, -1):
        idx = [i for i in np.where(part == 2)[0] if me.vertices[i].co.x * sd > 0]
        c = sum((me.vertices[i].co for i in idx), Vector()) / len(idx)
        axis = Vector((sd * 0.40, -0.88, 0.18)).normalized()
        for i in idx:
            v = me.vertices[i]; v.co = c + axis * FWD + (v.co - c) * S
        print('EYE', sd, 'verts', len(idx), 'centre', [round(x, 3) for x in c])
    me['eye_scale'] = S
    me.update()
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print('SAVED', name)
