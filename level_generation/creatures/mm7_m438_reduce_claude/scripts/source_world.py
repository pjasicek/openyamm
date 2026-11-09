"""Rest-pose world positions of work/source.blend Body (same vertex order as dump_mesh.py) -> work/source_world.npy,
for matching master labels by nearest vertex. Args: none"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
b = bpy.data.objects['Body']
np.save(os.path.join(HERE, 'work', 'source_world.npy'), np.array([tuple(b.matrix_world @ v.co) for v in b.data.vertices]))
print('WORLD', len(b.data.vertices), [round(x, 3) for x in b.matrix_world.translation], [round(x, 3) for x in b.matrix_world.to_euler()])
