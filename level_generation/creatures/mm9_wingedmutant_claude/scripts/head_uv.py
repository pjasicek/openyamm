"""Head texture set UVs (CLAUDE_CREATURE_TEXTURES.md "Head detail"; after ../mm9_yrsa_claude/v2/scripts/head_split.py).

On the symmetric grafted body (face attribute 'head' = 1: the grafted head's skin, eyes, teeth, hair locks and the
neck bridge): UV layer 'HeadUV' by Smart UV Project of the head faces; islands of the face skin, eyes and teeth are
scaled FACE_DENSITY times (linear) against the hair before packing, so the face gets most of the 1K head texture.
Exports the head faces alone (HeadUV as their only UV layer, neutral material) as the Meshy head retexture upload.
Args: -- <in blend> <out blend> <upload glb> [face density]"""
import bpy, bmesh, sys, os, math
import numpy as np

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD = a[:3]
FACE_DENSITY = float(a[3]) if len(a) > 3 else 1.8
SKIN_ANGLE = float(a[4]) if len(a) > 4 else 80.0
HAIR_ANGLE = float(a[5]) if len(a) > 5 else 85.0
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
me = body.data
head = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', head)
kind = np.zeros(len(me.vertices), np.int32)
me.attributes['kind'].data.foreach_get('value', kind)
if 'HeadUV' not in me.uv_layers:
    me.uv_layers.new(name='HeadUV')
me.uv_layers.active = me.uv_layers['HeadUV']
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='OBJECT')
fkind = np.array([np.bincount([kind[i] for i in p.vertices], minlength=5).argmax() for p in me.polygons])
skin_f = (head == 1) & ((fkind == 1) | (fkind == 0))          # skin shell and the neck bridge
# 1. the skin shell (face, skull, neck): Smart UV Project with a wide angle (few, nearly planar islands; an
#    angle-based unwrap of the whole shell shrank the dense face to a few per cent of the island)
co = np.array([tuple(v.co) for v in me.vertices])
yc = co[kind == 1][:, 1].mean()
for e in me.edges:
    i, j = e.vertices
    e.use_seam = bool(abs(co[i, 0]) < 1e-5 and abs(co[j, 0]) < 1e-5 and co[i, 1] > yc and co[j, 1] > yc
                      and kind[i] == 1 and kind[j] == 1)
for p in me.polygons:
    p.select = bool(skin_f[p.index])
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(SKIN_ANGLE), island_margin=0.004, area_weight=1.0,
                         scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
# 2. eyes, teeth and hair locks: Smart UV Project
for p in me.polygons:
    p.select = bool(head[p.index] and not skin_f[p.index])
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(HAIR_ANGLE), island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = bool(head[p.index])
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(me)
bm.faces.ensure_lookup_table()
uv = bm.loops.layers.uv['HeadUV']
hf = [f for f in bm.faces if head[f.index]]
parent = {f.index: f.index for f in hf}


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


for f in hf:
    for l in f.loops:
        e = l.edge
        for g in e.link_faces:
            if g is f or g.index not in parent:
                continue
            l2 = next(x for x in g.loops if x.edge == e)
            a1, b1 = l[uv].uv, l.link_loop_next[uv].uv
            a2, b2 = l2[uv].uv, l2.link_loop_next[uv].uv
            if ((a1 - b2).length < 1e-6 and (b1 - a2).length < 1e-6) or ((a1 - a2).length < 1e-6 and (b1 - b2).length < 1e-6):
                parent[find(f.index)] = find(g.index)
islands = {}
for f in hf:
    islands.setdefault(find(f.index), []).append(f)


def area3(isl):
    return sum(f.calc_area() for f in isl)


def area2(isl):
    t = 0.0
    for f in isl:
        p = [l[uv].uv for l in f.loops]
        for k in range(1, len(p) - 1):
            t += abs((p[k] - p[0]).cross(p[k + 1] - p[0])) / 2
    return t


# equal texel density for every island first (the angle-based skin island comes out at its own scale), then the
# face/skin, eyes and teeth FACE_DENSITY times denser than the hair
nface = 0
for isl in islands.values():
    a3, a2 = area3(isl), area2(isl)
    if a2 < 1e-12:
        continue
    k = math.sqrt(a3 / a2)
    hair = sum(1 for f in isl for v in f.verts if kind[v.index] == 3) > len(isl) * 1.5
    if not hair:
        k *= FACE_DENSITY; nface += 1
    pts = [l[uv].uv.copy() for f in isl for l in f.loops]
    c = sum(pts, pts[0] * 0) / len(pts)
    for f in isl:
        for l in f.loops:
            l[uv].uv = c + (l[uv].uv - c) * k
bmesh.update_edit_mesh(me)
bpy.ops.uv.select_all(action='SELECT')
try:
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True, shape_method='CONCAVE')
except TypeError:
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
for e in me.edges:
    e.use_seam = False
print('HEADUV islands', len(islands), 'face islands scaled', nface)

# upload: head faces alone, HeadUV only
ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
ob.parent = None; ob.matrix_world = body.matrix_world.copy()
for m in list(ob.modifiers):
    ob.modifiers.remove(m)
ob.vertex_groups.clear()
b2 = bmesh.new(); b2.from_mesh(ob.data); hl = b2.faces.layers.int['head']
bmesh.ops.delete(b2, geom=[f for f in b2.faces if f[hl] == 0], context='FACES')
bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
# upright for the retexture (the multiview head references are level): MM9's head up U -> +Z, forward -> -Y
J = {b.name: np.array(b.head_local) for b in rig.data.bones}
U = J['Bip01 Head'] - J['Bip01 Neck']; U /= np.linalg.norm(U)
Fh = np.array(rig.data.bones['Bip01 Head'].matrix_local.to_3x3())[:, 2]
Fh -= (Fh @ U) * U; Fh /= np.linalg.norm(Fh)
A = np.stack([U, Fh, np.cross(U, Fh)], 1)
B = np.stack([np.array([0, 0, 1.0]), np.array([0, -1.0, 0]), np.cross([0, 0, 1.0], [0, -1.0, 0])], 1)
R = B @ A.T
cen = np.mean([tuple(v.co) for v in b2.verts], 0)
for v in b2.verts:
    v.co = tuple(R @ (np.array(tuple(v.co)) - cen))
b2.to_mesh(ob.data); b2.free()
for l in [l.name for l in ob.data.uv_layers if l.name != 'HeadUV']:
    ob.data.uv_layers.remove(ob.data.uv_layers[l])
for at in [x.name for x in ob.data.attributes if not x.name.startswith('.') and x.name not in ('position', 'HeadUV')]:
    try:
        ob.data.attributes.remove(ob.data.attributes[at])
    except RuntimeError:
        pass
mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
ob.data.materials.clear(); ob.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=False, export_morph=False, export_attributes=False)
print('UPLOAD', UPLOAD, len(ob.data.polygons), 'faces')
bpy.data.objects.remove(ob, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
