"""X-ray overlay of a blend's Body against the MM9 mesh and bones: orthographic front/side/top silhouettes as PNG.
Args: blend, mm9 glb, out png"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
BL, MM9, OUT = argv
bpy.ops.wm.open_mainfile(filepath=BL)
b = bpy.data.objects['Body']
dg = bpy.context.evaluated_depsgraph_get()
ev = b.evaluated_get(dg).to_mesh()
bv = np.array([b.matrix_world @ v.co for v in ev.vertices]); bt = np.array([[l for l in p.vertices] for p in ev.polygons])
ex = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
new = [x for x in bpy.data.objects if x not in ex]
m = next(x for x in new if x.type == 'MESH' and 'd_lich' in x.name)
a = next(x for x in new if x.type == 'ARMATURE')
if a.animation_data:
    a.animation_data.action = None
for p in a.pose.bones:
    p.matrix_basis.identity()
bpy.context.view_layer.update()
mv = np.array([m.matrix_world @ v.co for v in m.data.vertices]); mt = np.array([list(p.vertices) for p in m.data.polygons])
bones = {x.name: (x.parent.name if x.parent else None, np.array(a.matrix_world @ x.head_local)) for x in a.data.bones}
np.savez(OUT + '.npz', bv=bv, bt=bt, mv=mv, mt=mt, names=list(bones), par=[bones[k][0] or '' for k in bones], pos=np.array([bones[k][1] for k in bones]))
