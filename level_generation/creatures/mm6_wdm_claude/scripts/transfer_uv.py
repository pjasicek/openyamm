"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto the rigged demon. The returned mesh has
the same faces, normalised (uniform scale, centred); it is fitted back by its bounding box, every rig face is matched
to the returned face with the same centroid, and each corner takes the UV of the matching returned corner (nearest
vertex). Run on work/rig_v1.blend; saves work/rig_uv.blend. Args: meshy job folder (default meshy/retexture_v2)."""
import bpy, os, sys
import numpy as np
from mathutils import Vector, kdtree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
job = args[0] if args else 'meshy/retexture_v2'
mesh = bpy.data.objects['Demon']; rig = bpy.data.objects['Demon_Rig']
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, job, 'model_urls_glb.glb'))
src = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
S = np.array([tuple(src.matrix_world @ v.co) for v in src.data.vertices])
T = np.array([tuple(mesh.matrix_world @ v.co) for v in mesh.data.vertices])
scale = (T.max(0) - T.min(0)).max() / (S.max(0) - S.min(0)).max()
offset = (T.max(0) + T.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale
S = S * scale + offset
suv = src.data.uv_layers.active.data
tree = kdtree.KDTree(len(src.data.polygons))
for p in src.data.polygons:
    tree.insert(Vector(S[list(p.vertices)].mean(0)), p.index)
tree.balance()
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
tuv = mesh.data.uv_layers.new(name='UVMap').data
worst = 0.0
for p in mesh.data.polygons:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, dist = tree.find(c)
    worst = max(worst, dist)
    sp = src.data.polygons[si]
    for li in p.loop_indices:
        tv = T[mesh.data.loops[li].vertex_index]
        best = min(sp.loop_indices, key=lambda sl: np.linalg.norm(S[src.data.loops[sl].vertex_index] - tv))
        tuv[li].uv = suv[best].uv
bpy.data.objects.remove(src, do_unlink=True)
print('TRANSFERRED faces', len(mesh.data.polygons), 'scale %.4f' % scale, 'worst centroid distance %.6f m' % worst)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_uv.blend'))
