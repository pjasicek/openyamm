"""The crown (work/crown.npz, make_crown.py) into Body: vertex attribute part 21, face attribute mat 3 (accessory set), rigid on Head,
UVs in PartUV (HeadUV and UVMap get the same, unused). Faces flat-shaded (hard-edged ice and metal). Args: <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = np.load(os.path.join(HERE, 'work', 'crown.npz'))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int['part']; dv = bm.verts.layers.deform.verify()
gi = body.vertex_groups.find('Bip01 Head')
nv = [bm.verts.new(tuple(p)) for p in Z['V']]
for x in nv: x[lay] = 21; x[dv][gi] = 1.0
layers = [bm.loops.layers.uv.get(n) for n in ('PartUV', 'UVMap', 'HeadUV')]
mt = bm.faces.layers.int.get('mat')
n = 0
for f in Z['F']:
    try:
        q = bm.faces.new([nv[i] for i in f])
    except ValueError:
        continue
    q.smooth = False; n += 1
    for l, i in zip(q.loops, f):
        for L in layers:
            if L is not None: l[L].uv = (float(Z['UV'][i, 0]), float(Z['UV'][i, 1]))
    if mt is not None: q[mt] = 3
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CROWN attached', len(nv), 'verts', n, 'faces')
