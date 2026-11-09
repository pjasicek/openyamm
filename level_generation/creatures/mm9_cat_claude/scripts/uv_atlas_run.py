"""Sharp-texture UVs (claude_shared/TEXTURE_QUALITY_PASS.md): xatlas charts packed by uv_atlas.py with the head charts
denser, plus two neutral static uploads for Meshy: the whole body, and the head islands alone on the SAME layout (the head
retexture paints only those islands, compose merges them into the one 2K map).
Args: <in blend> <out blend> <body upload glb> <head upload glb> <report json> <head groups comma> [head_factor]
xatlas packs differently per run: never re-run once the uploads went to Meshy."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'claude_shared'))
import uv_atlas
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UP_B, UP_H, REP, HG = argv[:6]
HF = float(argv[6]) if len(argv) > 6 else 2.5
HEAD = tuple(HG.split(','))
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
mesh = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
b0 = bmesh.new(); b0.from_mesh(mesh.data)
bmesh.ops.triangulate(b0, faces=[f for f in b0.faces if len(f.verts) > 3])   # the tongue and the eye spheres
b0.to_mesh(mesh.data); b0.free()
report = uv_atlas.unwrap(mesh, head_groups=HEAD, head_factor=HF)
print('UV_ATLAS', json.dumps(report))
me = mesh.data
# islands: faces sharing an edge with the same uv on both sides
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv['UVMap']
par = list(range(len(bm.faces)))


def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x


for e in bm.edges:
    if len(e.link_faces) != 2:
        continue
    f0, f1 = e.link_faces
    uv = []
    for f in (f0, f1):
        for l in f.loops:
            if l.edge == e:
                a, b = l[uvl].uv, l.link_loop_next[uvl].uv
                uv.append({l.vert.index: tuple(np.round(a, 6)), l.link_loop_next.vert.index: tuple(np.round(b, 6))})
    if uv[0] == uv[1]:
        par[find(f0.index)] = find(f1.index)
groups = [g.index for g in mesh.vertex_groups if g.name in HEAD]
hw = np.array([sum(g.weight for g in v.groups if g.group in groups) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
roots = np.array([find(i) for i in range(len(bm.faces))])
area = np.array([f.calc_area() for f in bm.faces])
fhw = np.array([hw[[v.index for v in f.verts]].mean() for f in bm.faces])
head_face = np.zeros(len(bm.faces), bool)
for r in np.unique(roots):
    m = roots == r
    if (area[m] * fhw[m]).sum() / area[m].sum() >= 0.5:
        head_face[m] = True
report['head_faces'] = int(head_face.sum()); report['faces'] = len(head_face)
a = me.attributes.new('head', 'INT', 'FACE') if 'head' not in me.attributes else me.attributes['head']
for i, v in enumerate(head_face):
    a.data[i].value = int(v)
bm.free()
json.dump(report, open(REP, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def export(path, keep_faces):
    dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
    dup.matrix_world = mesh.matrix_world
    bpy.context.scene.collection.objects.link(dup)
    if keep_faces is not None:
        b = bmesh.new(); b.from_mesh(dup.data); b.faces.ensure_lookup_table()
        bmesh.ops.delete(b, geom=[f for f in b.faces if not keep_faces[f.index]], context='FACES')
        b.to_mesh(dup.data); b.free()
    for g in list(dup.vertex_groups):
        dup.vertex_groups.remove(g)
    for o in bpy.data.objects:
        o.select_set(o == dup)
    bpy.context.view_layer.objects.active = dup
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                              export_animations=False, export_materials='NONE', export_attributes=False)
    bpy.data.objects.remove(dup)


export(UP_B, None)
export(UP_H, head_face)
print('UV done', report['faces'], report['head_faces'])
