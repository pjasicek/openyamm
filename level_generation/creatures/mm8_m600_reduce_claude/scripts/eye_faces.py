"""Rigid eye faces of the Nightmare (work/source.blend): faces whose three vertices carry > 0.999 weight on an
EmbeddedEye* or Eye*_Tip bone, the set mm8_m600_claude/scripts/build_lods.py protects (iris UVs) -> work/eye_faces.npy."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
eg = {g.index for g in o.vertex_groups if g.name.startswith('EmbeddedEye') or (g.name.startswith('Eye') and g.name.endswith('_Tip'))}
rigid = np.array([any(g.group in eg and g.weight > .999 for g in v.groups) for v in me.vertices])
faces = np.array([t.vertices[:] for t in me.loop_triangles])
keep = rigid[faces].all(1); np.save(os.path.join(HERE, 'work', 'eye_faces.npy'), keep)
print('EYES rigid vertices', int(rigid.sum()), 'faces', int(keep.sum()))
