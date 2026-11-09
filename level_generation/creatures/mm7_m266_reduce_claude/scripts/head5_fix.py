"""User review 2026-10-20 (head 5, the rust horned head): two short curved horns sat where the eyes should be and one
stray horn jutted down beside the upper fang; the head 5 HD master has orange eyes there and no horn by the mouth.
Removes those three separate horn pieces from the picked candidate (connected pieces rigid on Head5 whose centre lies
within 3 cm of the rest-space centres below) and, with REA_EYES=1, adds the eyes from work/head5_eyes.npz
(head5_eyes.py: low-poly lenses sunk into the sockets, rigid on Head5, UVs in the free sixth tile of the head atlas).
Usage: blender -b -P head5_fix.py -- <in blend> <cand> <out blend>"""
import os, sys, bpy, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; src_blend, cand, out = a[:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', src_blend))
ob = bpy.data.objects[cand]; me = ob.data
# rest-space centres (work/mesh_r78.npz pieces 170, 167, 176): eye horns at the hydra's right and left, the stray horn
HORNS = [(0.690, -1.187, 1.435), (0.905, -1.205, 1.436), (0.877, -1.327, 1.370)]
h5 = ob.vertex_groups['Head5'].index
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen, remove = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    comp, stack = [], [v]; seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); stack.append(y)
    if len(comp) > 300:
        continue
    c = np.mean([x.co[:] for x in comp], 0)
    rigid = all(any(g.group == h5 and g.weight > .99 for g in me.vertices[x.index].groups) for x in comp)
    for k, h in enumerate(HORNS):
        if rigid and np.linalg.norm(c - np.array(h)) < .03:
            remove.append((k, comp)); print('HORN', k, len(comp), 'verts at', np.round(c, 3).tolist(), flush=True)
assert sorted(k for k, _ in remove) == [0, 1, 2], 'expected exactly the three head 5 horns'
faces_before = len(bm.faces)
bmesh.ops.delete(bm, geom=[x for _, comp in remove for x in comp], context='VERTS')
print('REMOVED', faces_before - len(bm.faces), 'faces', flush=True)
if os.environ.get('REA_EYES') == '1':
    E = np.load(os.path.join(HERE, 'work', 'head5_eyes.npz'))
    uvl = bm.loops.layers.uv.active; dl = bm.verts.layers.deform.verify()
    heads_slot = next(i for i, m in enumerate(me.materials) if m.name.startswith('HydraHeads'))
    nv = [bm.verts.new(tuple(p)) for p in E['verts']]
    for v in nv:
        v[dl][h5] = 1.0
    bm.verts.ensure_lookup_table()
    added = 0
    for fi, tri in enumerate(E['faces']):
        f = bm.faces.new([nv[i] for i in tri]); f.material_index = heads_slot; f.smooth = True; added += 1
        for k, l in enumerate(f.loops):
            l[uvl].uv = tuple(E['uv'][fi * 3 + k])
    print('EYES', added, 'faces', len(nv), 'verts', flush=True)
bm.to_mesh(me); bm.free(); me.update()
print('TRIS', sum(len(p.vertices) - 2 for p in me.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', out))
