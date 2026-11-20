"""Forad on the playbook rig (2026-10-30 rework): the textured MM9-route body with the grafted MPFB hands and the head
split (work/head_v1.blend) becomes the playbook's step1 Body.

- rest pose, the MM9 armature and its weights dropped (the MPFB hand weights MP_* kept for mp_finger_weights.py);
  lifted so the soles are at z = 0 (MM9 space is centred on the pelvis), facing -Y as before;
- 'piece' (connected part) and 'garment' labels for weights_fix.py: 0 skin (the one-shell body and both hands),
  1 rigid head (eyes), 3 ponytail (+ its tie: head -> neck by height), 7 fittings (the necklace teeth and beads:
  rigid on the bone under them); 'orig_co' (the positions uploaded to Meshy's auto-rig);
- work/hand_openings.json: each wrist = the MPFB wrist joint the graft placed (graft_hands.py), anatomical sides
  (MM9's 'L' bones are on -X = the character's right);
- work/finger_joints.json: the MPFB hand joints mapped to the source names (B_<s>_Finger<i>, <i>1, <i>2 and the
  right thumb's B_R_Finger0.001/.002 quirk, with <distal>_tip), so build_rig.py fits every finger to its own chain.
Writes work/step1.blend and export/forad_clean_v1.glb (mesh only, for the Meshy auto-rig). Args: none"""
import bpy, bmesh, json, os
import numpy as np
V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(V2, 'work', *p)
bpy.ops.wm.open_mainfile(filepath=W('head_v1.blend'))
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = body.matrix_world.copy()
body.parent = None; body.matrix_world = mw
for m in list(body.modifiers):
    body.modifiers.remove(m)
me = body.data
me.transform(mw); body.matrix_world.identity()
co = np.array([tuple(v.co) for v in me.vertices])
lift = -float(co[:, 2].min())
for v in me.vertices:
    v.co.z += lift
co[:, 2] += lift
for g in [g for g in body.vertex_groups if not g.name.startswith('MP_')]:
    body.vertex_groups.remove(g)
G = json.load(open(W('hands_v1.json')))
head_z = float((rig.matrix_world @ rig.data.bones['Bip01 Head'].head_local).z) + lift
bpy.data.objects.remove(rig, do_unlink=True)
# parts
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(co), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
bm.free()
hand = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hand)
hand_v = set(v for p in me.polygons if hand[p.index] for v in p.vertices)
lab = {}
for k in range(cid):
    m = comp == k; n = int(m.sum()); c = co[m].mean(0); lo, hi = co[m].min(0), co[m].max(0)
    if n > 1000 or any(i in hand_v for i in np.where(m)[0][:5]):
        lab[k] = 0                                   # body shell, MPFB hands
    elif c[1] > 0.08 and c[2] > head_z - 0.2:
        lab[k] = 3                                   # ponytail and its tie (behind the head)
    elif lo[2] > head_z + 0.03 and n > 25:
        lab[k] = 1                                   # eyes
    else:
        lab[k] = 7                                   # necklace teeth and beads
gv = np.array([lab[c] for c in comp], np.int32)
for nm, val in (('piece', comp), ('garment', gv)):
    a = me.attributes.get(nm) or me.attributes.new(nm, 'INT', 'POINT'); a.data.foreach_set('value', val.tolist())
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('PREP lift', round(lift, 4), 'parts', cid, 'garments', {g: int((gv == g).sum()) for g in sorted(set(gv.tolist()))},
      'part labels', {g: sorted(k for k, x in lab.items() if x == g)[:12] for g in (1, 3)})
# wrists and fingers, anatomical sides
FJ, HO = {}, {}
for key, J in G['joints'].items():
    sd = 'L' if J['wrist'][0] > 0 else 'R'                # facing -Y: the character's left is +X
    P = {k: [v[0], v[1], v[2] + lift] for k, v in J.items()}
    HO[sd] = P['wrist']
    F = {}
    for f in range(1, 6):
        i = f - 1
        names = [f'B_{sd}_Finger{i}', f'B_{sd}_Finger{i}1', f'B_{sd}_Finger{i}2']
        if sd == 'R' and i == 0:
            names = ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
        for n, j in zip(names, (1, 2, 3)):
            F[n] = P[f'finger{f}-{j}']
        F[names[2] + '_tip'] = P[f'finger{f}-3_tip']
    FJ[sd] = F
json.dump(HO, open(W('hand_openings.json'), 'w'), indent=1)
json.dump(FJ, open(W('finger_joints.json'), 'w'), indent=1)
json.dump({'lift': lift}, open(W('prep.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=W('step1.blend'))
# Meshy auto-rig upload: mesh only
ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
for at in [a.name for a in ob.data.attributes if not a.name.startswith('.') and a.name not in ('position',)]:
    try:
        ob.data.attributes.remove(ob.data.attributes[at])
    except RuntimeError:
        pass
ob.vertex_groups.clear()
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
os.makedirs(os.path.join(V2, 'export'), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(V2, 'export', 'forad_clean_v1.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=False, export_attributes=False,
                          export_materials='NONE')
print('EXPORTED', 'forad_clean_v1.glb', 'height', round(float(co[:, 2].max()), 4))
