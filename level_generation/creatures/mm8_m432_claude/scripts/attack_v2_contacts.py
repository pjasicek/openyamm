"""Attack v2 arm contacts (the user's v1 finding: arms crossing, right upper arm through the pauldron), which g6
does not sample: upper arm, forearm and hand vertices of each side (half frames) against the closed body shell
without that arm (torso, other arm) and against each closed pauldron. args <blend> <action> ..."""
import bpy, bmesh, sys, json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
args = sys.argv[sys.argv.index('--') + 1:]
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / args[0])); rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
names = [g.name for g in body.vertex_groups]; w = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for e in v.groups: w[v.index, e.group] = e.weight
part = np.array([x.value for x in me.attributes['garment'].data]); faces = [tuple(f.vertices) for f in me.polygons]
rest = np.array([v.co[:] for v in me.vertices])
def wsum(keys, side=None):
    cols = [i for i, n in enumerate(names) if any(k in n for k in keys) and (side is None or n.startswith(f'B_{side}_'))]
    return w[:, cols].sum(1)
arm = {s: wsum(['Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger'], s) > .2 for s in 'LR'}
for g in np.unique(part):
    m = part == g; print('GARMENT', g, int(m.sum()), np.round(rest[m].mean(0), 3).tolist())
def closed(mask):
    mesh = bpy.data.meshes.new('S'); mesh.from_pydata([v.co[:] for v in me.vertices], [], [f for f in faces if all(mask[i] for i in f)])
    bm = bmesh.new(); bm.from_mesh(mesh); ids = bm.verts.layers.int.new('o')
    for v in bm.verts: v[ids] = v.index
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.triangulate(bm, faces=list(bm.faces)); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    out = [tuple(v[ids] for v in f.verts) for f in bm.faces]; bm.free(); bpy.data.meshes.remove(mesh); return out
# pauldrons: garment pieces centred at shoulder height, split by side
shoulder_z = (rig.data.bones['B_L_UpperArm'].head_local.z + rig.data.bones['B_R_UpperArm'].head_local.z) / 2
pauldrons = {}
for g in np.unique(part):
    m = part == g; c = rest[m].mean(0)
    if g not in (0, 1, 3) and abs(c[2] - shoulder_z) < .12 and m.sum() > 50:
        for s, sign in (('R', -1), ('L', 1)):
            ms = m & (np.sign(rest[:, 0]) == sign)
            if ms.sum() > 20: pauldrons[f'pauldron_{s}'] = ms
print('PAULDRONS', {k: int(v.sum()) for k, v in pauldrons.items()})
shells = {f'body_minus_{s}': closed(np.isin(part, [0, 1, 3]) & ~arm[s]) for s in 'LR'}
shells.update({k: closed(m) for k, m in pauldrons.items()})
samples = {}
for s in 'LR':
    head = np.array(rig.data.bones[f'B_{s}_UpperArm'].head_local)
    far = np.linalg.norm(rest - head, axis=1) > .14   # away from the filled shoulder cap
    samples[f'{s}_upperarm'] = (wsum(['UpperArm'], s) > .5) & far & np.isin(part, [0, 1, 3])
    samples[f'{s}_forearm'] = (wsum(['Forearm'], s) > .5) & np.isin(part, [0, 1, 3])
    samples[f'{s}_hand'] = wsum(['Hand', 'Finger'], s) > .5
report = {}
for an in args[1:]:
    ac = bpy.data.actions[an]; rig.animation_data.action = ac; rig.animation_data.action_slot = ac.slots[0]; worst = {}
    for f in np.arange(0, ac.frame_range[1] + .01, .5):
        bpy.context.scene.frame_set(int(f), subframe=float(f - int(f)))
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mm = ev.to_mesh(); co = [v.co.copy() for v in mm.vertices]; ev.to_mesh_clear()
        trees = {k: BVHTree.FromPolygons(co, fs) for k, fs in shells.items()}
        for key, mask in samples.items():
            s = key[0]
            for shell in [f'body_minus_{s}'] + [k for k in pauldrons if not k.endswith(s)]:
                tree = trees[shell]; label = f'{key}->{shell}'; count = 0
                for vi in np.where(mask)[0]:
                    p = co[vi]; loc, nrm, idx, dist = tree.find_nearest(p, .08)
                    if loc is not None and (p - loc).dot(nrm) < -.7 * dist and dist > .003:
                        count += 1
                        if dist > worst.get(label, {}).get('depth_m', .003):
                            hit = shells[shell][idx]
                            worst[label] = {'depth_m': round(dist, 4), 'frame': float(f), 'vertex': int(vi),
                                            'hit_bones': sorted({names[int(np.argmax(w[j]))] for j in hit})}
                if count:
                    entry = worst.setdefault(label + ' count', {'max': 0, 'frames': []})
                    entry['max'] = max(entry['max'], count); entry['frames'].append(float(f))
    report[an] = worst; print('CONTACTS', an, json.dumps(worst), flush=True)
out = P / 'work/attack_v2/arm_contacts.json'
old = json.loads(out.read_text()) if out.exists() else {}
old.update(report); out.write_text(json.dumps(old, indent=1))
