"""Add the fin leaves (build_fins.py npz) as object 'Fins' with UVs and an alpha-clipped material on the fin atlas.
Args: <in blend> <fins npz> <atlas png> <out blend>"""
import bpy, sys, os
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
IN, NPZ, ATLAS, OUT = argv
bpy.ops.wm.open_mainfile(filepath=IN)
d = np.load(NPZ)
if 'Fins' in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects['Fins'])
me = bpy.data.meshes.new('Fins')
me.from_pydata([tuple(v) for v in d['v']], [], [tuple(int(i) for i in t) for t in d['t']])
uv = me.uv_layers.new(name='UVMap')
for li, l in enumerate(me.loops):
    uv.data[li].uv = tuple(d['uv'][l.vertex_index])
fa = me.attributes.new('fin', 'INT', 'POINT'); ra = me.attributes.new('root', 'FLOAT', 'POINT')
for i in range(len(me.vertices)):
    fa.data[i].value = int(d['fin'][i]); ra.data[i].value = float(d['root'][i])
for p in me.polygons:
    p.use_smooth = True
ob = bpy.data.objects.new('Fins', me)
bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('FishFin')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.abspath(ATLAS))
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
try:
    mat.blend_method = 'CLIP'
except Exception:
    pass
try:
    mat.surface_render_method = 'DITHERED'
except Exception:
    pass
me.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINS ADDED', len(me.vertices), len(me.polygons))
