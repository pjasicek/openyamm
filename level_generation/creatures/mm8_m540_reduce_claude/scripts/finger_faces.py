"""Faces whose vertices are mostly finger-weighted (B_*_Finger*) -> work/keep_fingers.npy. Fingers in a shared cut
come back as jagged points (MM6 Dwarf); keep them exactly. Also faces on the cape bones (Cape0-2, weight > 0.5) ->
work/cape_faces.npy for a gentler cape ratio (its hem moved 27 mm at a 76 % cut). Run in Blender on work/source.blend."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; me = src.data; me.calc_loop_triangles()
fing = {g.index for g in src.vertex_groups if 'Finger' in g.name}
w = np.array([sum(g.weight for g in v.groups if g.group in fing) for v in me.vertices])
tris = np.array([t.vertices[:] for t in me.loop_triangles])
keep = w[tris].max(1) > .3
np.save(os.path.join(HERE, 'work', 'keep_fingers.npy'), keep); print('FINGERS kept', int(keep.sum()))
cape = {g.index for g in src.vertex_groups if g.name.startswith('Cape')}
cw = np.array([sum(g.weight for g in v.groups if g.group in cape) for v in me.vertices])
np.save(os.path.join(HERE, 'work', 'cape_faces.npy'), cw[tris].max(1) > .5); print('CAPE faces', int((cw[tris].max(1) > .5).sum()))
