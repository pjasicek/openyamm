"""Flying demon rig on the HD four-view Meshy mesh (work/hd_base.blend, rig frame, with wings).
Frame: raw Meshy mesh x2.8566 and lifted 0.8996 m (= the Meshy auto-rig frame, height 1.8 m, ground 0), forward -Y,
creature left +X. The mesh is symmetric about x = X0.
Skeleton (mixamorig names, so Meshy-library and Mixamo clips retarget by name):
  - limbs from the measured limb centrelines (measure_body.py) / Meshy rig_v2_body left joints, mirrored about X0,
  - spine on the midline (Hips -> Spine -> Spine1 -> Spine2 -> Neck -> Head), the head juts forward like the sprite,
  - wings: Wing_<S>_Root (Spine2) -> Wing_<S>_Arm -> Wing_<S>_Finger1..3 + Wing_<S>_Lead, joints read from the
    gridded views (wrist = top hook beside the head), depth sampled from the membrane.
Weights: Blender automatic (heat) weights for the body bones; wing vertices (work/wing_mask.npy) get inverse-distance
weights to the wing segments in the front plane; within SEAM_BAND of the body (along the mesh) they blend into
Spine2 (below LOW_Z: into the weights of the body vertex they grow from, over the wider LOW_BAND web, so the lower
membrane fans out from the waist instead of stretching into a sheet), and the back skin within BACK_BAND of the seam
(above the waist) blends into Spine2 as well; body heat weights are computed with the wing bones non-deforming;
separate pieces (spikes, claws, teeth) are bound rigidly to their nearest main-body vertex.
Saves work/rig_v1.blend."""
import bpy, bmesh, os
import numpy as np
from mathutils import Vector, kdtree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X0 = 0.0
SEAM_BAND = 0.10                  # m along the membrane over which the wing root follows the back (Spine2)
LOW_BAND, LOW_Z = 0.30, 1.12      # below LOW_Z the root follows the body skin it grows from over a wider web
BACK_BAND = 0.08                  # m along the back skin around the wing seam that also follows Spine2

mesh = bpy.data.objects['Demon']
for p in mesh.data.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in mesh.data.vertices])
wing = np.load(os.path.join(HERE, 'work', 'wing_mask.npy'))
assert len(wing) == len(co)


def mirror(p):
    return Vector((2 * X0 - p[0], p[1], p[2]))


def wing_y(x, z, side):
    """Membrane depth at (x, z): median y of nearby wing vertices on that side."""
    sel = wing & ((co[:, 0] - X0) * side > 0)
    d = np.hypot(co[sel, 0] - x, co[sel, 2] - z)
    near = np.argsort(d)[:12]
    return float(np.median(co[sel][near, 1]))


V = Vector
# body joints (left side; right = mirror)
SPINE = [V((0, -0.05, 0.86)), V((0, -0.05, 0.97)), V((0, -0.06, 1.05)), V((0, -0.07, 1.12)),
         V((0, -0.10, 1.18)), V((0, -0.15, 1.23)), V((0, -0.19, 1.36))]
ARM = [V((0.05, -0.07, 1.13)), V((0.19, -0.05, 1.14)), V((0.22, -0.07, 0.89)), V((0.30, -0.18, 0.66)),
       V((0.31, -0.25, 0.47))]
LEG = [V((0.08, -0.06, 0.88)), V((0.10, -0.10, 0.50)), V((0.12, -0.03, 0.21)), V((0.13, -0.15, 0.08)),
       V((0.13, -0.24, 0.02))]
# wing joints in the front plane (left side), read from the gridded front view
W_ROOT, W_ELBOW, W_WRIST = (0.09, 1.20), (0.11, 1.33), (0.125, 1.45)   # hook at the wrist, from the gridded views
W_TIPS = {'Lead': (0.70, 1.80), 'Finger1': (0.678, 1.549), 'Finger2': (0.588, 1.305), 'Finger3': (0.372, 1.157)}
print('WING joints root', W_ROOT, 'elbow', W_ELBOW, 'wrist', W_WRIST)

arm_data = bpy.data.armatures.new('Demon_Rig')
rig = bpy.data.objects.new('Demon_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones


def chain(names, pts, parent=None, connect_first=False):
    prev = eb[parent] if parent else None
    for i, n in enumerate(names):
        b = eb.new(n); b.head = pts[i]; b.tail = pts[i + 1]
        b.parent = prev; b.use_connect = prev is not None and (i > 0 or connect_first)
        prev = b
    return prev


chain(['mixamorig:Hips', 'mixamorig:Spine', 'mixamorig:Spine1', 'mixamorig:Spine2', 'mixamorig:Neck',
       'mixamorig:Head'], SPINE)
for side, sg, f in (('Left', 1, lambda p: p), ('Right', -1, mirror)):
    chain([f'mixamorig:{side}Shoulder', f'mixamorig:{side}Arm', f'mixamorig:{side}ForeArm', f'mixamorig:{side}Hand'],
          [f(p) for p in ARM], 'mixamorig:Spine2')
    chain([f'mixamorig:{side}UpLeg', f'mixamorig:{side}Leg', f'mixamorig:{side}Foot', f'mixamorig:{side}ToeBase'],
          [f(p) for p in LEG], 'mixamorig:Hips')
    s = 'L' if sg > 0 else 'R'

    def wp(xz):
        x = xz[0] if sg > 0 else 2 * X0 - xz[0]
        return V((x, wing_y(x, xz[1], sg), xz[1]))
    root = wp(W_ROOT); root.y = max(root.y, -0.05)
    chain([f'Wing_{s}_Root', f'Wing_{s}_Arm'], [root, wp(W_ELBOW), wp(W_WRIST)], 'mixamorig:Spine2')
    for k, tip in W_TIPS.items():
        b = eb.new(f'Wing_{s}_{k}'); b.head = wp(W_WRIST); b.tail = wp(tip); b.parent = eb[f'Wing_{s}_Arm']
for b in eb:
    b.align_roll(Vector((0, 0, 1)) if abs((b.tail - b.head).normalized().z) < 0.9 else Vector((0, -1, 0)))
bpy.ops.object.mode_set(mode='OBJECT')

for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
for b in rig.data.bones:                         # body heat weights must not see the wing bones
    b.use_deform = not b.name.startswith('Wing_')
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
for b in rig.data.bones:
    b.use_deform = True
    if b.name.startswith('Wing_') and b.name not in mesh.vertex_groups:
        mesh.vertex_groups.new(name=b.name)

# ---- weight cleanup ---------------------------------------------------------------------------------------------
groups = {g.name: g for g in mesh.vertex_groups}
gname = {g.index: g.name for g in mesh.vertex_groups}
import heapq
body_w = {}
for v in mesh.data.vertices:
    if not wing[v.index]:
        ws = {gname[g.group]: g.weight for g in v.groups if not gname[g.group].startswith('Wing_')}
        tot = sum(ws.values())
        if tot > 1e-6:
            body_w[v.index] = {k: w / tot for k, w in ws.items()}
# Seam band: geodesic distance (along mesh edges) from the body into each wing, and the body vertex it comes from.
adj = [[] for _ in range(len(co))]
for e in mesh.data.edges:
    a, b = e.vertices; d = float(np.linalg.norm(co[a] - co[b]))
    adj[a].append((b, d)); adj[b].append((a, d))
seam_d = np.full(len(co), np.inf); seam_src = np.full(len(co), -1)
heap = []
for i in body_w:
    if any(wing[j] for j, _ in adj[i]):
        seam_d[i] = 0.0; seam_src[i] = i; heap.append((0.0, i))
heapq.heapify(heap)
while heap:
    d, a = heapq.heappop(heap)
    if d > seam_d[a] or d > LOW_BAND:
        continue
    for b, w in adj[a]:
        if wing[b] and d + w < seam_d[b]:
            seam_d[b] = d + w; seam_src[b] = seam_src[a]; heapq.heappush(heap, (d + w, b))
wing_groups = [n for n in groups if n.startswith('Wing_')]
body_groups = [n for n in groups if not n.startswith('Wing_')]
verts = mesh.data.vertices
for side, s in ((1, 'L'), (-1, 'R')):
    segs = {}
    for b in rig.data.bones:
        if b.name.startswith(f'Wing_{s}_'):
            h, t = rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local
            segs[b.name] = (np.array([h.x, h.z]), np.array([t.x, t.z]))
    idx = np.nonzero(wing & ((co[:, 0] - X0) * side > 0))[0]
    for i in idx:
        p = co[i, [0, 2]]
        w = {}
        for n, (a, b) in segs.items():
            t = np.clip(np.dot(p - a, b - a) / max(np.dot(b - a, b - a), 1e-9), 0, 1)
            d = np.linalg.norm(p - (a + t * (b - a)))
            w[n] = 1.0 / (d * d + 0.04 ** 2)
        top = sorted(w.items(), key=lambda kv: -kv[1])[:3]
        tot = sum(v for _, v in top)
        src = int(seam_src[i])
        lz = float(np.clip((LOW_Z + 0.10 - co[src, 2]) / 0.20, 0, 1)) if src >= 0 else 0.0
        low = lz * lz * (3 - 2 * lz)                   # 1 below LOW_Z-0.1, 0 above LOW_Z+0.1, smooth between
        band = SEAM_BAND + (LOW_BAND - SEAM_BAND) * low
        u = float(np.clip(1.0 - seam_d[i] / band, 0, 1)) if src >= 0 else 0.0
        share = u * u * (3 - 2 * u)                    # near the seam the wing root moves with the back
        for g in groups.values():
            g.remove([int(i)])
        for n, v in top:
            groups[n].add([int(i)], (1 - share) * v / tot, 'REPLACE')
        if share > 0:
            for n, v in body_w[src].items():
                groups[n].add([int(i)], share * low * v, 'ADD')
            groups['mixamorig:Spine2'].add([int(i)], share * (1 - low), 'ADD')
# Back skin around the wing seam (shoulder blades) follows Spine2 too, fading out over BACK_BAND along the body, so
# the shoulder bone's motion does not tear the seam.
back_d = np.full(len(co), np.inf)
heap = [(0.0, i) for i in body_w if seam_d[i] == 0.0]
for _, i in heap:
    back_d[i] = 0.0
heapq.heapify(heap)
while heap:
    d, a = heapq.heappop(heap)
    if d > back_d[a] or d > BACK_BAND:
        continue
    for b, w in adj[a]:
        if b in body_w and d + w < back_d[b]:
            back_d[b] = d + w; heapq.heappush(heap, (d + w, b))
for i, ws in body_w.items():
    if back_d[i] <= BACK_BAND and co[i, 2] > 1.25:
        u = 1.0 - back_d[i] / BACK_BAND; k = u * u * (3 - 2 * u)
        new = {n: v * (1 - k) for n, v in ws.items()}
        new['mixamorig:Spine2'] = new.get('mixamorig:Spine2', 0.0) + k
        for n, v in new.items():
            groups[n].add([i], v, 'REPLACE')
body_idx = [int(i) for i in np.nonzero(~wing)[0]]
for n in wing_groups:
    groups[n].remove(body_idx)

# separate pieces: rigid to the nearest main-body vertex
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
seen = [False] * len(bm.verts); islands = []
for v in bm.verts:
    if seen[v.index]:
        continue
    st = [v]; comp = []; seen[v.index] = True
    while st:
        a = st.pop(); comp.append(a.index)
        for e in a.link_edges:
            b = e.other_vert(a)
            if not seen[b.index]:
                seen[b.index] = True; st.append(b)
    islands.append(comp)
bm.free()
islands.sort(key=len, reverse=True)
tree = kdtree.KDTree(len(islands[0]))
for i in islands[0]:
    tree.insert(verts[i].co, i)
tree.balance()
for comp in islands[1:]:
    anchor = min((tree.find(verts[i].co) for i in comp), key=lambda hit: hit[2])[1]
    weights = [(g.group, g.weight) for g in verts[anchor].groups]
    for g in mesh.vertex_groups:
        g.remove(comp)
    for gi, w in weights:
        mesh.vertex_groups[gi].add(comp, w, 'REPLACE')
empty = [v.index for v in verts if not v.groups or sum(g.weight for g in v.groups) < 1e-4]
print('EMPTY before fallback', len(empty), 'wing', int(wing[empty].sum()) if empty else 0,
      'z', np.round(co[empty, 2].min(), 2) if empty else '-', np.round(co[empty, 2].max(), 2) if empty else '-')
full = kdtree.KDTree(len(verts) - len(empty))
es = set(empty)
for v in verts:
    if v.index not in es:
        full.insert(v.co, v.index)
full.balance()
for i in empty:
    src = full.find(verts[i].co)[1]
    for g in verts[src].groups:
        mesh.vertex_groups[g.group].add([i], g.weight, 'REPLACE')
empty = [v.index for v in verts if not v.groups or sum(g.weight for g in v.groups) < 1e-4]
print('RIG bones', len(rig.data.bones), 'islands rebound', len(islands) - 1, 'unweighted', len(empty))
for b in ('Wing_L_Root', 'Wing_L_Arm', 'Wing_L_Lead', 'Wing_L_Finger1', 'Wing_L_Finger2', 'Wing_L_Finger3'):
    bb = rig.data.bones[b]; print('WB', b, tuple(round(c, 3) for c in bb.head_local), tuple(round(c, 3) for c in bb.tail_local))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_hd.blend'))
