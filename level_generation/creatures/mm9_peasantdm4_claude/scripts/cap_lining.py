"""Inner lining of the cap (PeasantDM4 see-through gate, 2026-11-02): Meshy's skullcap shell has gaps (the view passes
through its near wall and meets the back of the far wall: red/white wedges above the band) and an open bottom rim (a
red line between band and hair from below). The cap's loose part (head faces, connected to the highest head vertex) is
duplicated OFFSET inward along the vertex normals, flipped, with the same UVs (every layer), attributes and weights,
so every view into the cap meets painted cap faces. Positions/faces added only. Args (Blender): <in blend> <out blend>
[offset 0.003]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
src, dst = a[0], a[1]; OFF = float(a[2]) if len(a) > 2 else 0.003
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hl = bm.faces.layers.int.get('head')
hv = [v for f in bm.faces if f[hl] == 1 for v in f.verts]
top = max(hv, key=lambda v: v.co.z)
part = set(); st = [top]
while st:
    v = st.pop()
    if v in part: continue
    part.add(v)
    for e in v.link_edges:
        st.append(e.other_vert(v))
faces = [f for f in bm.faces if all(v in part for v in f.verts)]
zs = [v.co.z for v in part]
print('CAP part verts', len(part), 'faces', len(faces), 'z', round(min(zs), 3), round(max(zs), 3))
dl = bm.verts.layers.deform.active
vmap = {}
for v in part:
    nv = bm.verts.new(v.co - v.normal * OFF)
    if dl: nv[dl] = v[dl]
    vmap[v] = nv
bm.verts.index_update()
uvl = list(bm.loops.layers.uv.values())
ints = list(bm.faces.layers.int.values())
new = []
for f in faces:
    vs = [vmap[v] for v in reversed(f.verts)]
    nf = bm.faces.new(vs)
    nf.material_index = f.material_index; nf.smooth = f.smooth
    for L in ints: nf[L] = f[L]
    src_loops = list(reversed(f.loops))
    for nl, ol in zip(nf.loops, src_loops):
        for U in uvl: nl[U].uv = ol[U].uv
    new.append(nf)
bm.normal_update()
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst)
print('CAP_LINING faces', len(new), 'offset', OFF)
