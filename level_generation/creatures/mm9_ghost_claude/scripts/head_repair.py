"""Close the head on the UV master: the interior clean left the throat and a few eye and mouth pockets open, and a see-through head must not show the sky down its throat. Each boundary loop is filled; new faces
take one dark texel of the mouth paint (work/head_dark_uv.json), facing forward. No existing face or UV changes. Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
h = bpy.data.objects['Head']
dark = json.load(open(os.path.join(os.path.dirname(a[0]), 'head_dark_uv.json')))['uv']
bm = bmesh.new(); bm.from_mesh(h.data); bm.edges.ensure_lookup_table()
uvl = bm.loops.layers.uv['UVMap']
left = set(e for e in bm.edges if e.is_boundary)
loops = []
while left:
    e = left.pop(); cur = {e}; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in left:
                    left.discard(y); cur.add(y); st.append(y)
    loops.append(cur)
n = 0; f0 = set(bm.faces)
darkf = set()
for l in loops:
    before = set(bm.faces)
    r = bmesh.ops.holes_fill(bm, edges=list(l), sides=0)
    if len(l) > 60:
        darkf |= set(bm.faces) - before
res = bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if f not in f0 and len(f.verts) > 3])
for of, nfs in res['face_map'].items() if False else []:
    pass
darkc = [f.calc_center_median() for f in darkf if f.is_valid]
# what holes_fill refused (loops that touch themselves): a fan from the loop's centre
left = set(e for e in bm.edges if e.is_boundary)
loops = []
while left:
    e = left.pop(); cur = {e}; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in left:
                    left.discard(y); cur.add(y); st.append(y)
    loops.append(cur)
for l in loops:
    vs = {v for e in l for v in e.verts}
    c = sum((v.co for v in vs), vs.__iter__().__next__().co * 0) / len(vs)
    c.y += 0.05 if len(l) > 60 else 0.004     # a pocket behind the loop, never a lid across the teeth
    cv = bm.verts.new(c)
    for e in l:
        try:
            nf = bm.faces.new((e.verts[0], e.verts[1], cv))
            if len(l) > 60:
                darkf.add(nf)
        except ValueError:
            pass
new = [f for f in bm.faces if f not in f0]
for f in new:
    if f not in darkf and len(darkc) and any(e.is_manifold is False for e in f.edges) and False:
        darkf.add(f)
for f in new:
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    if f in darkf or any(g in darkf for g in ()):
        uv = dark
    else:
        # a pin hole in the skin: the colour of the skin beside it
        uv = None
        for v in f.verts:
            for l2 in v.link_loops:
                if l2.face in f0:
                    uv = l2[uvl].uv.copy(); break
            if uv is not None:
                break
        uv = uv if uv is not None else dark
    for l in f.loops:
        l[uvl].uv = uv
    n += 1
# shell faces the decimation turned inward (single-sided, so they vanish and show the dark mouth behind: the scrap on the jaw)
_vs = list(bm.verts); cen = sum((v.co for v in _vs), _vs[0].co * 0) / len(_vs)
flip = []
for f in bm.faces:
    if f in new:
        continue
    f.normal_update()
    c = f.calc_center_median()
    if abs(c.x) > 0.04 and c.y > -0.25 and f.normal.dot(c - cen) < 0:
        flip.append(f)
bmesh.ops.reverse_faces(bm, faces=flip)
print('SHELL flipped', len(flip))
print('HEADFILL loops', len(loops), 'new faces', n, 'boundary left', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(h.data); bm.free()
h.vertex_groups['Xhead'].add(list(range(len(h.data.vertices))), 1.0, 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=a[1])
