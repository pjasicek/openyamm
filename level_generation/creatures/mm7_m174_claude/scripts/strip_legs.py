"""Remove the legs inside the floor-length robe (creature.json strip_legs: skin piece vertices below below_z within
|x| < inside_abs_x): Smart Topology modelled the body under the skirt, and skinned legs would poke through the robe
chains in every step (the robe is carried by its own chains; the leg bones stay for the robe's leg capsules). Runs
after prepare_rig.py (the auto-rig saw the whole body). Edits work/step1.blend in place. Args: none"""
import bpy, bmesh, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg, common
L = cfg.C.get('strip_legs')
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1.blend'))
body = bpy.data.objects['Body']; me = body.data
pv = np.array([a.value for a in me.attributes['piece'].data]); co = np.array([v.co[:] for v in me.vertices])
kill = (pv == L['piece']) & (co[:, 2] < L['below_z']) & (np.abs(co[:, 0]) < L['inside_abs_x'])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.where(kill)[0]], context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
print('STRIPLEGS removed verts', int(kill.sum()), 'left', len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1.blend'))
