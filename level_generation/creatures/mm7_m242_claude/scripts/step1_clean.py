"""Step 1 for the m242 Smart Topology return (work/st_v1_parts.blend: 227 loose parts, normalised to 1.85 m from the
lowest robe shred to the hood peak, facing -Y). Every part is joined into 'Body' with point attributes 'piece' (part
number), 'cloth' (1 = a sheet: the hood/cape shell P01 and the robe shreds, whose border edges number more than 0.6 x
its vertices; 0 = a bone piece) and
'orig_co'. Parts with fewer than MIN_TRIS triangles are dropped (slivers). Then the joints are measured on the bone
pieces (no Meshy auto-rig: the playbook's skeleton rule) and written to work/joints_final.json in build_rig.py's
names:
- spine: the vertebral column P04 (x ~ 0, z 1.14..1.66) sampled at fixed fractions for Pelvis, Spine, Spine1,
  Spine2, Neck; Head at the top of the column under the skull (P00);
- arms: the humerus (largest closed piece per side between |x| 0.2 and 0.45): its principal-axis ends give the
  shoulder (medial) and the elbow (lateral); the forearm (closed pieces between the elbow and |x| 0.62): its far end is
  the wrist; the hand = the finger bones beyond; clavicle from beside the neck base to the shoulder;
- legs: there are none; Thigh/Calf/Foot/Toe joints are placed inside the robe (hip 9 cm off the pelvis, knee 0.62,
  ankle 0.12, toe 12 cm ahead) only so the source clips retarget; they carry no weight.
Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
MIN_TRIS = int(os.environ.get('MIN_TRIS', '4'))
# hidden fins behind the ribcage and the nape (inside the robe at rest; closed, so first filed as bones and rigid on the
# spine, they poked up out of the hood when the head bent forward: user review 2026-10-20, hood_back_spike.png)
DROP = {190, 202}
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
info = {}
for n, o in list(P.items()):
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if tris < MIN_TRIS or int(n[1:]) in DROP:
        bpy.data.objects.remove(o, do_unlink=True); P.pop(n); continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    nb = sum(1 for e in bm.edges if e.is_boundary)
    # a robe shred is a ribbon: almost every vertex lies on its border (boundary/verts ~ 1); bones are closed or have
    # a few open rims (humerus 39/110, forearm 11/51); the hood/cape shell P01 is one big open sheet (277/678)
    open_ = int(n[1:]) == 1 or nb > 0.6 * len(bm.verts)
    bm.free()
    co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    # some shreds are closed ribbons: every real bone sits above the pelvis (z > 1.1) and is short, so a piece centred
    # below 1.12 m or spanning more than 0.3 m vertically is cloth
    open_ = open_ or co[:, 2].mean() < 1.12 or np.ptp(co[:, 2]) > 0.3
    info[int(n[1:])] = {'co': co, 'cloth': open_}
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.data.attributes.new('cloth', 'INT', 'POINT').data.foreach_set('value', [int(open_)] * len(o.data.vertices))
    o.data.materials.clear()
for o in bpy.data.objects:
    o.select_set(o.name in P)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active; body.name = body.data.name = 'Body'
co = np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN parts', len(info), 'cloth', sum(v['cloth'] for v in info.values()), 'tris',
      sum(len(p.vertices) - 2 for p in body.data.polygons))


def ends(c):
    m = c.mean(0); u = np.linalg.svd(c - m, full_matrices=False)[2][0]; t = (c - m) @ u
    return m + u * t.min(), m + u * t.max()


J = {}
spine = info[4]['co']; z0, z1 = spine[:, 2].min(), spine[:, 2].max()
def on_spine(z):
    s = spine[np.abs(spine[:, 2] - z) < 0.02]
    return [float(s[:, 0].mean()), float(s[:, 1].mean()), float(z)]
for name, f in (('Pelvis', 0.03), ('Spine', 0.18), ('Spine1', 0.38), ('Spine2', 0.58), ('Neck', 0.80)):
    J[name] = on_spine(z0 + f * (z1 - z0))
J['Head'] = on_spine(z1 - 0.01)
bones = {k: v for k, v in info.items() if not v['cloth']}
for s, sg in (('L', 1.0), ('R', -1.0)):
    cand = [(len(v['co']), k) for k, v in bones.items() if 0.2 < sg * v['co'].mean(0)[0] < 0.45 and v['co'][:, 2].mean() > 1.2]
    hum = max(cand)[1]
    a, b = ends(bones[hum]['co'])
    sh, el = (a, b) if sg * a[0] < sg * b[0] else (b, a)
    fore = [k for k, v in bones.items() if sg * el[0] - 0.03 < sg * v['co'].mean(0)[0] < 0.62 and k != hum and v['co'][:, 2].mean() > 1.15]
    fc = np.vstack([bones[k]['co'] for k in fore])
    wr = fc[np.argmax(sg * fc[:, 0])]
    hand = np.vstack([v['co'] for k, v in bones.items() if sg * v['co'].mean(0)[0] > 0.6 and v['co'][:, 2].mean() > 1.0])
    J[f'{s}_UpperArm'] = sh.tolist(); J[f'{s}_Forearm'] = el.tolist(); J[f'{s}_Hand'] = wr.tolist()
    J[f'{s}_Clavicle'] = [float(sg * 0.035 + J['Neck'][0]), float(J['Spine2'][1]), float(J['Spine2'][2] + 0.04)]
    J[f'{s}_Thigh'] = [float(J['Pelvis'][0] + sg * 0.09), float(J['Pelvis'][1]), float(J['Pelvis'][2] - 0.04)]
    J[f'{s}_Calf'] = [float(J['Pelvis'][0] + sg * 0.1), float(J['Pelvis'][1]), 0.62]
    J[f'{s}_Foot'] = [float(J['Pelvis'][0] + sg * 0.1), float(J['Pelvis'][1] + 0.02), 0.12]
    J[f'{s}_Toe0'] = [float(J['Pelvis'][0] + sg * 0.1), float(J['Pelvis'][1] - 0.12), 0.04]
    print('JOINTS', s, 'humerus P%02d' % hum, 'shoulder', np.round(sh, 3), 'elbow', np.round(el, 3), 'wrist', np.round(wr, 3),
          'forearm pieces', len(fore), 'hand verts', len(hand), 'hand tip x', round(float(sg * hand[:, 0].max()), 3))
# closed pieces away from the skeleton are cloth shreds (P196/P210 under the arms were filed as bones): a bone piece
# lies within ENVELOPE m of the spine column, an arm line (shoulder-elbow-wrist-hand tip) or inside the skull box
ENVELOPE = float(os.environ.get('ENVELOPE', '0.07'))
def seg_d(p, a, b):
    a, b = np.array(a), np.array(b); t = np.clip(((p - a) @ (b - a)) / max((b - a) @ (b - a), 1e-9), 0, 1)
    return float(np.linalg.norm(p - (a + t * (b - a))))
segs = [(J['Pelvis'], J['Head'])]
for s_ in ('L', 'R'):
    tip = np.array(J[f'{s_}_Hand']) + (np.array(J[f'{s_}_Hand']) - np.array(J[f'{s_}_Forearm'])) * 0.9
    segs += [(J[f'{s_}_Clavicle'], J[f'{s_}_UpperArm']), (J[f'{s_}_UpperArm'], J[f'{s_}_Forearm']), (J[f'{s_}_Forearm'], J[f'{s_}_Hand']), (J[f'{s_}_Hand'], tip)]
sk = info[0]['co']; sk_lo, sk_hi = sk.min(0) - 0.01, sk.max(0) + 0.01
recl = []
for k, v in info.items():
    if v['cloth'] or k == 0:
        continue
    c = v['co'].mean(0)
    near_ribs = abs(c[0] - J['Pelvis'][0]) < 0.17 and J['Pelvis'][2] - 0.03 < c[2] < J['Neck'][2]
    claws = abs(c[0]) > 0.5                                      # the curled phalanges reach beyond the hand line
    if not near_ribs and not claws and not (np.all(c > sk_lo) and np.all(c < sk_hi)) and min(seg_d(c, a, b) for a, b in segs) > ENVELOPE:
        recl.append(k); v['cloth'] = True
pv_ = np.zeros(len(body.data.vertices), np.int32); body.data.attributes['piece'].data.foreach_get('value', pv_)
clv = np.array([int(info[p]['cloth']) for p in pv_], np.int32)
body.data.attributes['cloth'].data.foreach_set('value', clv.tolist())
print('CLEAN dropped hidden fins', sorted(DROP), '| reclassified as cloth (away from the skeleton):', recl)
print('JOINTS spine', {k: [round(x, 3) for x in J[k]] for k in ('Pelvis', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head')})
json.dump({'joints': J, 'source': 'pieces (step1_clean.py)'}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
