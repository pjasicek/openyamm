"""Back faces for the open wing membranes: Meshy built each membrane as one open sheet, which the engine culls from
behind. Every open wing component (faces mostly weighted to Yw* bones, with boundary edges) gets a copy with the
same weights and UVs, its winding flipped and moved OFFSET metres to its back along the vertex normals (the
claude_shared lining fix of mm6_cle: an exact offset copy, not a second shell).
Args: <in blend> <out blend> [offset]"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = argv[0], argv[1]
OFFSET = float(argv[2]) if len(argv) > 2 else 0.002
bpy.ops.wm.open_mainfile(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
ob = bpy.data.objects['Body']
gn = {g.index: g.name for g in ob.vertex_groups}
wing = [sum(g.weight for g in v.groups if gn[g.group].startswith('Yw')) for v in ob.data.vertices]
bm = bmesh.new(); bm.from_mesh(ob.data)
wf = {f for f in bm.faces if sum(wing[v.index] for v in f.verts) / len(f.verts) > 0.5}
seen = set(); sel = []
for f in list(wf):
    if f in seen:
        continue
    st = [f]; seen.add(f); comp = []
    while st:
        x = st.pop(); comp.append(x)
        for e in x.edges:
            for g in e.link_faces:
                if g in wf and g not in seen:
                    seen.add(g); st.append(g)
    if any(e.is_boundary for x in comp for e in x.edges):
        sel += comp
nrm = {}
for f in sel:
    for v in f.verts:
        nrm[v] = v.normal.copy()
res = bmesh.ops.duplicate(bm, geom=sel)
vmap = res['vert_map']
new_faces = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
for old, new in vmap.items():
    if isinstance(old, bmesh.types.BMVert) and old in nrm:
        new.co = old.co - nrm[old] * OFFSET
bmesh.ops.reverse_faces(bm, faces=new_faces)
bm.to_mesh(ob.data)
print('BACKFACES', len(sel), 'faces copied')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
