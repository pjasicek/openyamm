"""Clean glowing eyes: one small ellipsoid dome (front half) against the back wall of each skull socket (centres from the Ghost's eye
ellipses and sockets), rigid on B_Head, joined into the reduced mesh (work/ladder_head.blend -> work/ladder_eyes.blend).
Their UVs fill one empty square of the head layout (work/eye_block.json), which compose_head.py paints the constant
eye colour with the eye mask; the socket surfaces keep their own (dark) texture, so the glow outline is the
ellipsoid's silhouette at every angle. Usage: blender -b -P add_eyes.py"""
import json, math, os, bmesh, bpy
import numpy as np
from mathutils import Matrix, Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EYES = [(.01542, 2.0873), (-.04194, 2.0877)]       # x, z of the eye ellipses (compose_ghost.py)
CY = float(os.environ.get('REA_EYE_Y', '-.041'))   # dome base depth (socket back wall about -.03, brow rim -.068)
RADII = tuple(float(v) for v in os.environ.get('REA_EYE_RADII', '.0128,.0075,.0105').split(','))  # x, y, z (m)

# empty square in the head layout: coverage raster of the head UVs
d = np.load(os.path.join(HERE, 'work', 'head_uv.npz')); N = 256
cov = np.zeros((N, N), bool)
for t in d['uv']:
    lo = np.floor(t.min(0) * N).astype(int) - 1; hi = np.ceil(t.max(0) * N).astype(int) + 1
    cov[max(lo[1], 0):hi[1] + 1, max(lo[0], 0):hi[0] + 1] = True
size = 6  # cells of 4 texels at 1K
free = [(x, y) for y in range(2, N - size - 2) for x in range(2, N - size - 2) if not cov[y:y + size, x:x + size].any()]
assert free, 'no free square for the eyes'
bx, by = free[0]; block = [bx / N, by / N, (bx + size) / N, (by + size) / N]
json.dump({'uv_min': block[:2], 'uv_max': block[2:]}, open(os.path.join(HERE, 'work', 'eye_block.json'), 'w'))
print('EYE block', block)

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_head.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
cand = bpy.data.objects['Cand_55']; inv = cand.matrix_world.inverted()
bm = bmesh.new(); bm.from_mesh(cand.data)
uvl = bm.loops.layers.uv.active; deform = bm.verts.layers.deform.verify()
head_group = cand.vertex_groups['B_Head'].index
W, G, H = 2080, 32, 1024
lo, hi = Vector(block[:2]), Vector(block[2:]); pad = (hi - lo) * .15
for x, z in EYES:
    # front dome (poles on the view axis, back half removed): a smooth 20-gon outline at 100 triangles per eye
    ret = bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=6, radius=1.0)
    verts = ret['verts']
    bmesh.ops.rotate(bm, verts=verts, matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    back = [v for v in verts if v.co.y > 1e-4]
    bmesh.ops.delete(bm, geom=back, context='VERTS'); verts = [v for v in verts if v.is_valid]
    m = inv @ Matrix.Translation((x, CY, z)) @ Matrix.Diagonal((*RADII, 1))
    bmesh.ops.transform(bm, matrix=m, verts=verts)
    faces = {f for v in verts for f in v.link_faces}
    for v in verts:
        v[deform].clear(); v[deform][head_group] = 1.0
    for f in faces:
        f.smooth = True; f.material_index = 0
        for loop in f.loops:  # front projection into the eye square (constant colour, so only the area matters)
            p = cand.matrix_world @ loop.vert.co
            s = Vector(((p.x - x) / RADII[0] * .5 + .5, (p.z - z) / RADII[2] * .5 + .5))
            u = lo + pad + Vector((s.x * (hi - lo - 2 * pad).x, s.y * (hi - lo - 2 * pad).y))
            loop[uvl].uv = ((H + G + u.x * H) / W, u.y)
bm.to_mesh(cand.data); bm.free(); cand.data.update()
print('EYES added tris', sum(len(p.vertices) - 2 for p in cand.data.polygons) - 9425,
      'total', sum(len(p.vertices) - 2 for p in cand.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_eyes.blend'))
