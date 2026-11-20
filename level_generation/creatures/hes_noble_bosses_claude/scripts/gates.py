"""Numeric gates for one boss on every clip (12 samples per second), from work/<boss>/assembled.blend:
  shell stretch: edge-length ratio of the shell triangles against the rest pose (p99, max; Trooper limits 1.10/1.25);
  skin poke: body vertices more than 4 mm outside the shell within 3 cm of it (counted against the rest pose's own);
  weapon in body: weapon points (the attachment on Weapon_R) more than 5 mm inside the body skin, away from the hands;
  add-on in body: rigid add-on points (coils, cables, crown) more than 5 mm inside the body or shell, except the
      embedded roots (points within 2 cm of the body or shell at rest);
  shell edges shorter than 2 mm at rest are left out of the stretch.
Shell / body / add-on vertices are told apart by material. Usage (Blender): gates.py <boss> [weapon.glb]
Writes review/gates_<boss>.json."""
import bpy, bmesh, sys, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index('--') + 1:]
boss = args[0]; weapon = args[1] if len(args) > 1 else None
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / f'work/{boss}/assembled.blend'))
sc = bpy.context.scene
rig = bpy.data.objects['Rig']; noble = bpy.data.objects['Noble']
me = noble.data
mats = [m.name if m else '' for m in me.materials]
fmat = np.array([p.material_index for p in me.polygons])
kind = np.array(['shell' if mats[i].endswith('_Shell') else 'addon' if '_Add' in mats[i] else 'body' for i in fmat])
F = [list(p.vertices) for p in me.polygons]
vkind = np.array(['body'] * len(me.vertices), dtype=object)
for f, k in zip(F, kind):
    for v in f:
        if k != 'body':
            vkind[v] = k
gid = {g.name: g.index for g in noble.vertex_groups}
hand = np.zeros(len(me.vertices))
for v in me.vertices:
    hand[v.index] = sum(g.weight for g in v.groups if noble.vertex_groups[g.group].name.startswith(('B_L_Hand', 'B_R_Hand', 'B_L_Finger', 'B_R_Finger')))
shell_edges = np.array([(f[i], f[(i + 1) % len(f)]) for f, k in zip(F, kind) if k == 'shell' for i in range(len(f))])
wobj = None
if weapon:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(Path(weapon).resolve()))
    wobj = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
    WL = np.array([tuple(wobj.matrix_world @ v.co) for v in wobj.data.vertices])   # glTF->Blender converted
    # the attachment's file coordinates are the Weapon_R node frame (glTF); the importer turned them into Blender
    # world = (x, -z, y); undo to node-local glTF, then map through the joint's glTF frame per frame below
    WL = np.stack([WL[:, 0], WL[:, 2], -WL[:, 1]], 1)
    sel = np.linspace(0, len(WL) - 1, min(400, len(WL))).astype(int); WL = WL[sel]
# Weapon_R node frame in glTF from the exported LOD0 (rest), and its pose-relative motion from the rig
import struct
raw = (P / f'export/{boss}_lod0.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
from mathutils import Quaternion


def node_world(name):
    parent = {c: i for i, nd in enumerate(doc['nodes']) for c in nd.get('children', [])}
    i = next(k for k, nd in enumerate(doc['nodes']) if nd.get('name') == name); M = Matrix.Identity(4)
    while i is not None:
        nd = doc['nodes'][i]; r = nd.get('rotation', (0, 0, 0, 1))
        M = Matrix.LocRotScale(Vector(nd.get('translation', (0, 0, 0))), Quaternion((r[3], r[0], r[1], r[2])),
                               Vector(nd.get('scale', (1, 1, 1)))) @ M
        i = parent.get(i)
    return M


G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))     # glTF world -> Blender world
W_rest_gltf = node_world('Weapon_R') if weapon else None


def evaluate():
    dg = bpy.context.evaluated_depsgraph_get(); ev = noble.evaluated_get(dg).data
    return np.array([tuple(noble.matrix_world @ v.co) for v in ev.vertices])


rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
REST = evaluate()
rest_len = np.linalg.norm(REST[shell_edges[:, 0]] - REST[shell_edges[:, 1]], axis=1)
rest_hand_M = (rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix).copy()
body_faces = [f for f, k in zip(F, kind) if k == 'body']
shell_faces = [f for f, k in zip(F, kind) if k == 'shell']


def bvh(verts, faces):
    return BVHTree.FromPolygons([tuple(v) for v in verts], faces, all_triangles=False)


def poke_count(V):
    sb = bvh(V, shell_faces); cnt = 0
    for i in np.flatnonzero(vkind == 'body'):
        if hand[i] > 0.5:
            continue
        loc, nrm, fi, d = sb.find_nearest(Vector(V[i]), 0.03)
        if loc is not None and (Vector(V[i]) - loc).dot(nrm) > 0.004:
            cnt += 1
    return cnt


rest_poke = poke_count(REST)
# add-on roots are embedded on purpose (cables into the spine plates and forearm, crown spikes into the skull):
# only add-on points at least 2 cm outside the body+shell at rest are tested
_sb = bvh(REST, body_faces + shell_faces)
embedded = np.zeros(len(REST), bool)
for i in np.flatnonzero(vkind == 'addon'):
    loc, nrm, fi, d = _sb.find_nearest(Vector(REST[i]), 0.02)
    embedded[i] = loc is not None
report = {'boss': boss, 'rest_skin_poke': rest_poke, 'clips': {}}
for act in sorted((a for a in bpy.data.actions if a.name.startswith('Noble_')), key=lambda a: a.name):
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    end = act.frame_range[1]; worst = {'stretch_p99': 0, 'stretch_max': 0, 'skin_poke': 0, 'weapon_in_body_mm': 0,
                                      'addon_in_body_mm': 0}
    for t in np.arange(0, end / 24 + 1e-6, 1 / 12):
        sc.frame_set(int(t * 24), subframe=(t * 24) % 1); bpy.context.view_layer.update()
        V = evaluate()
        L = (np.linalg.norm(V[shell_edges[:, 0]] - V[shell_edges[:, 1]], axis=1) / np.maximum(rest_len, 1e-6))[rest_len > 0.002]
        worst['stretch_p99'] = max(worst['stretch_p99'], float(np.percentile(L, 99)))
        worst['stretch_max'] = max(worst['stretch_max'], float(L.max()))
        worst['skin_poke'] = max(worst['skin_poke'], poke_count(V) - rest_poke)
        bb = bvh(V, body_faces)
        sbv = bvh(V, body_faces + shell_faces)
        for i in np.flatnonzero((vkind == 'addon') & ~embedded)[::3]:
            loc, nrm, fi, d = sbv.find_nearest(Vector(V[i]), 0.05)
            if loc is not None and (Vector(V[i]) - loc).dot(nrm) < -0.005:
                worst['addon_in_body_mm'] = max(worst['addon_in_body_mm'], d * 1000)
        if weapon:
            Mh = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
            # the weapon rides the hand: rest weapon frame moved by the hand's pose delta
            Mw = Mh @ rest_hand_M.inverted() @ G2B @ W_rest_gltf
            for p in WL:
                q = Mw @ Vector(p)
                loc, nrm, fi, d = bb.find_nearest(q, 0.08)
                if loc is None:
                    continue
                vi = F[body_faces and 0 or 0][0]
                if (q - loc).dot(nrm) < -0.005:
                    # skip contacts at the hands (the grip)
                    near = np.linalg.norm(V - np.array(q), axis=1).argmin()
                    if hand[near] < 0.3:
                        worst['weapon_in_body_mm'] = max(worst['weapon_in_body_mm'], d * 1000)
    report['clips'][act.name] = {k: round(v, 3) for k, v in worst.items()}
    print('GATE', act.name, report['clips'][act.name], flush=True)
(P / 'review').mkdir(exist_ok=True)
(P / f'review/gates_{boss}.json').write_text(json.dumps(report, indent=1))
print('GATES DONE', boss)
