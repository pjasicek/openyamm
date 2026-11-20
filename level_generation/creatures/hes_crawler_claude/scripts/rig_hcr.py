"""Acid Crawler rig from the Meshy Smart Topology mesh. Saves work/rig_v1.blend. Forward -Y, up +Z, the crawler's
left +X.

1. Import, apply transforms, level the body (the eight claw tips lay on a plane pitched ~6 deg head-down in the Meshy
   return: rotate about X so that plane is horizontal), ground the tips at z = 0.
2. Classify the 29 connected pieces by geometry: the body (head, flanks, thick upper legs), 7 dorsal plates + the
   head shield, 2 mandibles, 2 eyes, per leg an ankle ring and a clawed foot.
3. LOD0 reduction per part (Decimate collapse, limited by vertex group): the face, mandibles and eyes keep their
   density, flat plates and the leg tubes lose the most (budget 5-8k triangles).
4. Bones. Spine: Body (root, mid-body) -> Thorax -> Head (mandibles, sac, mouth socket) and Body -> Abdomen -> Tail;
   the bone borders sit in the gaps between dorsal plates. Legs L1..L4 / R1..R4 (front to back): Femur (hip inside the
   flank -> the ankle ring) and Tibia (ring -> claw tip; ring and foot ride it rigidly). Sac (throat, jiggle), Mandible_L/R,
   Socket_Mouth (acid spit release, non-deforming).
5. Weights: automatic (heat) weights on the body piece; every other piece rigid on one bone (plates on the spine bone
   whose span holds them, ring and foot on the Tibia, eyes and shield on Head, mandibles on their bones); the throat sac
   region blends onto Sac."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'Crawler'
mesh.data.materials.clear()
for p in mesh.data.polygons:
    p.use_smooth = True


def components():
    bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
    label = -np.ones(len(bm.verts), int); k = 0
    for v in bm.verts:
        if label[v.index] >= 0:
            continue
        st = [v]; label[v.index] = k
        while st:
            x = st.pop()
            for e in x.link_edges:
                w = e.other_vert(x)
                if label[w.index] < 0:
                    label[w.index] = k; st.append(w)
        k += 1
    bm.free()
    return label


def coords():
    return np.array([tuple(v.co) for v in mesh.data.vertices])


def classify(co, label):
    """Part name per piece from its size and position."""
    n = label.max() + 1
    counts = np.bincount(label, minlength=n)
    body = int(np.argmax(counts))
    parts = {body: 'body'}
    cen = {k: co[label == k].mean(0) for k in range(n)}
    lows = {k: co[label == k, 2].min() for k in range(n)}
    for k in range(n):
        if k == body:
            continue
        c = cen[k]
        if abs(c[0]) < 0.02 and c[2] > 0.2:
            parts[k] = 'plate'
        elif abs(c[0]) > 0.15:
            parts[k] = 'legpiece'
        elif counts[k] > 70:
            parts[k] = 'mandible_L' if c[0] > 0 else 'mandible_R'
        else:
            parts[k] = 'eye'
    # leg pieces: per side, sort by y into four legs; the lower piece of each pair is the foot
    for s, sgn in (('L', 1), ('R', -1)):
        ks = sorted([k for k, p in parts.items() if p == 'legpiece' and np.sign(cen[k][0]) == sgn], key=lambda k: cen[k][1])
        assert len(ks) == 8, (s, ks)
        for i in range(4):
            pair = sorted(ks[2 * i:2 * i + 2], key=lambda k: lows[k])
            # pairs by y order can interleave: re-pair by nearest centroids
            parts[pair[0]] = f'foot_{s}{i + 1}'; parts[pair[1]] = f'ring_{s}{i + 1}'
    return body, parts, cen


# ---------------------------------------------------------------- 1. level and ground
label = components()
co = coords()
body, parts, cen = classify(co, label)
tips = []
for k, p in parts.items():
    if p.startswith('foot_'):
        q = co[label == k]
        tips.append(q[np.argsort(q[:, 2])[:6]].mean(0))
tips = np.array(tips)
A = np.c_[np.ones(len(tips)), tips[:, 1], tips[:, 0]]
a, b, c = np.linalg.lstsq(A, tips[:, 2], rcond=None)[0]
pitch = math.atan(b)                                   # z rises toward +y (rear) by b per metre
R = Matrix.Rotation(-pitch, 4, 'X')                    # +X rotation lifts -y... rotate so the rear comes down
mesh.data.transform(R)
co = coords()
tips_after = (np.array(R.to_3x3()) @ tips.T).T
zmin = float(tips_after[:, 2].min())
mesh.data.transform(Matrix.Translation((0, 0, -zmin)))
co = coords()
print('LEVEL pitch %.2f deg, tips z before' % math.degrees(pitch), np.round(tips[:, 2], 3), 'after',
      np.round(tips_after[:, 2] - zmin, 3), 'mesh zmin', round(float(co[:, 2].min()), 4))

# ---------------------------------------------------------------- 3. LOD0 reduction per part
KEEP = {'body': 0.42, 'plate': 0.55, 'shield': 0.75, 'ring': 0.5, 'foot': 0.5, 'mandible': 0.75, 'eye': 1.0}


def part_kind(p, k):
    if p == 'plate' and cen[k][1] < -0.38:
        return 'shield'
    return p.split('_')[0]


mesh.data.calc_loop_triangles()
tri_before = len(mesh.data.loop_triangles)
for kind, keep in KEEP.items():
    if keep >= 1.0:
        continue
    label = components(); co = coords()
    body, parts, cen = classify(co, label)
    sel = np.array([part_kind(parts[int(l)], int(l)) == kind for l in label])
    w = sel.astype(float)
    if kind == 'body':
        # the face and throat keep their density: weight 0 at the front, ramping in behind the head
        w *= np.clip((co[:, 1] + 0.40) / 0.08, 0.0, 1.0)
    g = mesh.vertex_groups.new(name='Dec')
    for i in np.nonzero(w > 0)[0]:
        g.add([int(i)], float(w[i]), 'REPLACE')
    mesh.data.calc_loop_triangles()
    total = len(mesh.data.loop_triangles)
    tri_vert = np.array([t.vertices[0] for t in mesh.data.loop_triangles])
    part_tris = int(sel[tri_vert].sum())
    mod = mesh.modifiers.new('Dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'; mod.ratio = (total - part_tris * (1 - keep)) / total
    mod.vertex_group = 'Dec'; mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='Dec')
    mesh.vertex_groups.remove(mesh.vertex_groups['Dec'])
    mesh.data.calc_loop_triangles()
    print('DECIMATE', kind, part_tris, '->', part_tris - (total - len(mesh.data.loop_triangles)), 'total',
          len(mesh.data.loop_triangles), flush=True)
mesh.data.calc_loop_triangles()
print('TRIS', tri_before, '->', len(mesh.data.loop_triangles))

# ---------------------------------------------------------------- 2. classify the reduced mesh
label = components(); co = coords()
body, parts, cen = classify(co, label)
assert sum(1 for p in parts.values() if p == 'plate') == 8, parts
pts = lambda k: co[label == k]
byname = {}
for k, p in parts.items():
    byname.setdefault(p, []).append(k)
plates = sorted(byname['plate'], key=lambda k: cen[k][1])          # front (shield) to rear
plate_y = [float(cen[k][1]) for k in plates]
gaps = [(plate_y[i] + plate_y[i + 1]) / 2 for i in range(len(plates) - 1)]
print('PLATES y', np.round(plate_y, 3), 'gaps', np.round(gaps, 3))


def junction(pa, pb, n=20):
    d = np.linalg.norm(pa[:, None, :] - pb[None, :, :], axis=2)
    f = np.argsort(d, axis=None)[:n]
    i, j = np.unravel_index(f, d.shape)
    return ((pa[i] + pb[j]) / 2).mean(0)


bodyp = pts(body)


_ys = np.linspace(float(bodyp[:, 1].min()) + 0.03, float(bodyp[:, 1].max()) - 0.03, 25)
_zs = []
for _y in _ys:
    _s = bodyp[(np.abs(bodyp[:, 0]) < 0.06) & (np.abs(bodyp[:, 1] - _y) < 0.04)]
    _zs.append((np.percentile(_s[:, 2], 2) + np.percentile(_s[:, 2], 98)) / 2)
_mid = np.polyfit(_ys, _zs, 3)


def midline_z(y):
    """Body centre height: a cubic fitted to the belly/back midpoints along the body."""
    return float(np.polyval(_mid, y))


# spine borders in the plate gaps: Head | Thorax | Body | Abdomen | Tail
Y_FRONT, Y_HEAD, Y_THORAX, Y_BODY, Y_ABD, Y_REAR = (float(co[:, 1].min()), gaps[0], gaps[2], gaps[4], gaps[6],
                                                    float(co[:, 1].max()))
SPINE = [('Tail', Y_ABD, Y_REAR), ('Abdomen', Y_BODY, Y_ABD), ('Body', Y_BODY, Y_THORAX),
         ('Thorax', Y_THORAX, Y_HEAD), ('Head', Y_HEAD, Y_FRONT + 0.03)]
JOINTS = {}
for s in 'LR':
    for i in range(1, 5):
        ring, foot = byname[f'ring_{s}{i}'][0], byname[f'foot_{s}{i}'][0]
        knee = junction(bodyp, pts(ring))                 # the tube meets the ankle ring
        q = pts(foot)
        tip = q[np.argsort(q[:, 2])[:6]].mean(0)
        # hip: centre of the leg tube's cross-section where it leaves the flank (|x| 0.115..0.135 near the leg's y)
        sgn = 1 if s == 'L' else -1
        tube = bodyp[(sgn * bodyp[:, 0] > 0.095) & (sgn * bodyp[:, 0] < 0.14) & (np.abs(bodyp[:, 1] - knee[1]) < 0.07)]
        # the cross-section nearest the hip-knee line: the 30 tube vertices closest to the knee's y and height
        tube = tube[np.argsort(np.abs(tube[:, 1] - knee[1]) + 0.5 * np.abs(tube[:, 2] - knee[2] - 0.06))[:30]]
        hip = tube.mean(0) if len(tube) else np.array([np.nan] * 3); hip[0] = sgn * 0.10
        JOINTS[f'{s}{i}'] = [hip, knee, tip]
for leg, j in JOINTS.items():                          # mirror a failed hip from the other side
    if not np.all(np.isfinite(j[0])):
        o = JOINTS[('R' if leg[0] == 'L' else 'L') + leg[1]][0].copy(); o[0] = -o[0]; j[0] = o
    print('JOINT', leg, [np.round(p, 3).tolist() for p in j])

arm = bpy.data.armatures.new('Crawler_Rig')
rig = bpy.data.objects.new('Crawler_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, head, tail, parent=None, connect=False, deform=True):
    b = eb.new(name); b.head = Vector(head); b.tail = Vector(tail); b.parent = parent; b.use_connect = connect
    b.use_deform = deform
    d = (b.tail - b.head).normalized()
    b.align_roll(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, -1, 0)))
    return b


def sp(y):
    return Vector((0.0, y, midline_z(y)))


B = {}
B['Body'] = bone('Body', sp(Y_BODY), sp(Y_THORAX))
B['Thorax'] = bone('Thorax', sp(Y_THORAX), sp(Y_HEAD), B['Body'], True)
head_tip = sp(Y_FRONT + 0.03)
B['Head'] = bone('Head', sp(Y_HEAD), head_tip, B['Thorax'], True)
B['Abdomen'] = bone('Abdomen', sp(Y_BODY), sp(Y_ABD), B['Body'])
B['Tail'] = bone('Tail', sp(Y_ABD), sp(Y_REAR - 0.02), B['Abdomen'], True)
for s in 'LR':
    k = byname[f'mandible_{s}'][0]; q = pts(k)
    top = q[np.argsort(-q[:, 2])[:10]].mean(0); tipm = q[np.argsort(q[:, 2])[:10]].mean(0)
    bone(f'Mandible_{s}', top, tipm, B['Head'])
# throat sac: the low front of the head piece under the mouth
front = bodyp[(bodyp[:, 1] < Y_FRONT + 0.07) & (np.abs(bodyp[:, 0]) < 0.06)]
zmouth = float(np.percentile(front[:, 2], 45))
sac = bodyp[(bodyp[:, 1] < Y_FRONT + 0.10) & (np.abs(bodyp[:, 0]) < 0.07) & (bodyp[:, 2] < zmouth)]
sac_c = sac.mean(0)
bone('Sac', Vector((0, sac_c[1] + 0.04, sac_c[2] + 0.02)), Vector((0, sac_c[1] - 0.03, sac_c[2] - 0.02)), B['Head'])
mouth = Vector((0.0, float(bodyp[:, 1].min()) - 0.005, zmouth + 0.02))
bone('Socket_Mouth', mouth, mouth + Vector((0, -0.05, 0)), B['Head'], deform=False)
LEG_PARENT = {1: 'Thorax', 2: 'Body', 3: 'Body', 4: 'Abdomen'}
for leg, (hip, knee, tip) in JOINTS.items():
    f = bone(f'Femur_{leg}', hip, knee, B[LEG_PARENT[int(leg[1])]])
    bone(f'Tibia_{leg}', knee, tip, f, True)
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- 5. weights
# Heat weights on the body piece alone (a temporary copy), then rigid pieces.
for o in bpy.data.objects:
    o.select_set(False)
tmp = mesh.copy(); tmp.data = mesh.data.copy(); bpy.context.scene.collection.objects.link(tmp)
bpy.context.view_layer.objects.active = tmp
tmp.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(tmp.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if label[v.index] != body], context='VERTS')
bmesh.update_edit_mesh(tmp.data)
bpy.ops.object.mode_set(mode='OBJECT')
for bn in ('Socket_Mouth', 'Mandible_L', 'Mandible_R', 'Sac'):
    arm.bones[bn].use_deform = False
rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
for bn in ('Mandible_L', 'Mandible_R', 'Sac'):
    arm.bones[bn].use_deform = True
body_idx = np.nonzero(label == body)[0]
groups = {b.name: mesh.vertex_groups.new(name=b.name) for b in arm.bones if b.use_deform}
tg = {g.index: g.name for g in tmp.vertex_groups}
unweighted = 0
for j, i in enumerate(body_idx):
    ws = [(tg[g.group], g.weight) for g in tmp.data.vertices[j].groups if g.weight > 1e-4]
    if not ws:
        unweighted += 1
        continue
    for name, w in ws:
        groups[name].add([int(i)], w, 'REPLACE')
bpy.data.objects.remove(tmp, do_unlink=True)
# throat sac: blend the low front head vertices onto Sac (weight by distance from the sac centre)
sac_r = 0.06
for i in body_idx:
    p = co[i]
    if p[1] < Y_FRONT + 0.12 and abs(p[0]) < 0.08 and p[2] < zmouth + 0.01:
        w = float(np.clip(1.4 - np.linalg.norm(p - sac_c) / sac_r, 0, 1))
        if w > 0:
            for g in mesh.vertex_groups:
                if g.name != 'Sac':
                    try:
                        g.add([int(i)], g.weight(int(i)) * (1 - w), 'REPLACE')
                    except RuntimeError:
                        pass
            groups['Sac'].add([int(i)], w, 'REPLACE')


def spine_bone(y):
    for name, y0, y1 in SPINE:
        if min(y0, y1) <= y <= max(y0, y1):
            return name
    return 'Head' if y < Y_HEAD else 'Tail'


for k, p in parts.items():
    if k == body:
        continue
    idx = [int(i) for i in np.nonzero(label == k)[0]]
    if p == 'plate':
        owner = spine_bone(float(cen[k][1]))
    elif p.startswith(('ring_', 'foot_')):
        owner = 'Tibia_' + p.split('_')[1]
    elif p.startswith('mandible_'):
        owner = 'Mandible_' + p[-1]
    else:
        owner = 'Head'
    groups[owner].add(idx, 1.0, 'REPLACE')
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
mesh.parent = rig
mesh.data.calc_loop_triangles()
info = {'pitch_deg': math.degrees(pitch), 'triangles': len(mesh.data.loop_triangles),
        'spine': {n: [y0, y1] for n, y0, y1 in SPINE}, 'plates_y': plate_y,
        'joints': {leg: [list(map(float, p)) for p in pts_] for leg, pts_ in JOINTS.items()},
        'sac_centre': sac_c.tolist(), 'mouth': list(mouth), 'parts': {str(k): p for k, p in parts.items()},
        'unweighted_body': unweighted}
json.dump(info, open(os.path.join(WORK, 'rig_info.json'), 'w'), indent=1)
print('RIGGED bones', len(arm.bones), 'tris', len(mesh.data.loop_triangles), 'unweighted body', unweighted,
      'unweighted all', sum(1 for v in mesh.data.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'rig_v1.blend'))
