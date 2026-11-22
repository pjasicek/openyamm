"""Textured views of the single foot with an image on it: -- <image in textures/ or abs> <prefix> [blend] [object]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
img_path = a[0] if os.path.isabs(a[0]) else os.path.join(HERE, 'textures', a[0])
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[2] if len(a) > 2 else 'foot_uv.blend'))
ob = bpy.data.objects[a[3] if len(a) > 3 else 'Foot']
mat = bpy.data.materials.new('m'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(img_path)
nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
ob.data.materials.clear(); ob.data.materials.append(mat)
import numpy as np
co = np.array([ob.matrix_world @ v.co for v in ob.data.vertices]); c = (co.min(0) + co.max(0)) / 2
s = float(np.ptp(co, 0).max()) * 1.15
V = {'front': (0, -3, 0), 'side': (3, 0, 0), 'top': (0, 0.001, 3), 'quarter': (2, -2.4, 1.4), 'under': (0, 0.001, -3),
     'oside': (-3, 0, 0)}
for k, off in V.items():
    C.render(tuple(c + off), tuple(c), s, os.path.join(HERE, 'review', f'{a[1]}_{k}.png'), res=(520, 420), floor=False,
             textured=True, extra=(ob.name,))
print('VIEWS', a[1])
