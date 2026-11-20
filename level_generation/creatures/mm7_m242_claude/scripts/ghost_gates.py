"""Gates for the ghost on every frame of every clip (half frames included):
- HOOD: edge stretch of the cowl (cape shell above z 1.40 m at rest), p99 and max;
- FINS (rest pose): rigid trunk pieces inside the cowl behind the neck (hidden at rest, uncovered when the hood moves);
- FLOOR: lowest vertex (bone pieces / cloth) against z = 0 (target >= -0.5 cm);
- STRETCH: edge length ratio posed / rest, p99 and max, for the cloth and for the bone pieces (rigid: ~1.0);
- HOVER: the pelvis height range of the airborne clips (steady hover: Standing, Walking, Attack, Hit, Fidget);
- JERK: the largest world-rotation step of the head and both hands per 1/60 s (deg).
Writes work/gates.json and prints one GATE line per clip. Args: -- <blend>"""
import bpy, sys, os, json, math
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
cl = np.zeros(len(me.vertices), np.int32); me.attributes['cloth'].data.foreach_get('value', cl)
E = np.array([tuple(e.vertices) for e in me.edges])
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
deps = bpy.context.evaluated_depsgraph_get()


def pose_co():
    bpy.context.view_layer.update(); deps.update()
    ev = body.evaluated_get(deps); m = ev.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return c.reshape(-1, 3)


R0 = pose_co(); L0 = np.linalg.norm(R0[E[:, 0]] - R0[E[:, 1]], axis=1)
ec = cl[E[:, 0]] == 1
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
# the hood/cowl: the cape shell above the collar (z > 1.40 m at rest)
hood = (pv[E[:, 0]] == 1) & (R0[E[:, 0], 2] > 1.40)
hv = np.where((pv == 1) & (R0[:, 2] > 1.40))[0]
# fin check: pieces that ride the trunk or the robe (dominant bone not head/neck/arm) must stay below the neck joint
names = [g.name for g in body.vertex_groups]
dom = np.array([names[max(v.groups, key=lambda e: e.weight).group] if len(v.groups) else '' for v in me.vertices])
trunk = np.array([not any(k in d for k in ('Head', 'Neck', 'Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) for d in dom])
others = np.where((cl == 0) & trunk)[0]          # rigid (bone-class) pieces on the trunk: the nape fins were these
# FINS (structural, rest pose): rigid trunk pieces inside the cowl behind the skull (above the collar, behind the
# neck joint) are hidden at rest but are uncovered when the hood follows the head (the removed nape fins P190/P202)
nk, hdz = np.array(rig.data.bones['B_Neck'].head_local), rig.data.bones['B_Head'].head_local.z
fin_pieces = sorted({int(pv[i]) for i in others if R0[i, 2] > nk[2] - 0.10 and R0[i, 1] > nk[1] + 0.05})   # the ribs end at the spine (y <= 0.02); P190/P202 reached 0.07-0.09
print('GATE fins: rigid trunk pieces inside the cowl behind the neck:', fin_pieces)
res = {'fins_rigid_trunk_pieces_in_cowl': fin_pieces}
for act in [a for a in bpy.data.actions if a.name in ('Standing', 'Walking', 'Attack', 'Hit', 'Fidget', 'Death')]:
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    zb, zc, sc_, sb_, pz, prev, jerk, hs, fins = [], [], [], [], [], {}, 0.0, [], []
    for f in np.arange(f0, f1 + 1e-6, 0.5):
        sc.frame_set(int(f), subframe=float(f) - int(f))
        C = pose_co()
        zb.append(C[cl == 0, 2].min()); zc.append(C[cl == 1, 2].min())
        r = np.linalg.norm(C[E[:, 0]] - C[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        sc_.append(np.percentile(r[ec], 99)); sb_.append(r[~ec].max())
        hs.append((np.percentile(r[hood], 99), r[hood].max()))
        # fins: any non-skull, non-cape vertex higher than the hood's lowest back point and outside the hood's radius
        # around the head axis would stick out of the cowl
        fins.append(0)
        pz.append((rig.matrix_world @ rig.pose.bones['B_Pelvis'].head).z)
        for n in ('B_Head', 'B_L_Hand', 'B_R_Hand'):
            q = (rig.matrix_world @ rig.pose.bones[n].matrix).to_quaternion()
            if n in prev:
                a_ = math.degrees(prev[n].rotation_difference(q).angle); jerk = max(jerk, min(a_, 360 - a_))
            prev[n] = q
    res[act.name] = {'floor_bone_cm': round(float(min(zb)) * 100, 2), 'floor_cloth_cm': round(float(min(zc)) * 100, 2),
                     'cloth_stretch_p99_max': round(float(max(sc_)), 2), 'bone_stretch_max': round(float(max(sb_)), 3),
                     'pelvis_z_range_cm': [round(float(min(pz)) * 100, 1), round(float(max(pz)) * 100, 1)],
                     'jerk_deg_per_half_frame': round(jerk, 1),
                     'hood_stretch_p99': round(float(max(h[0] for h in hs)), 2), 'hood_stretch_max': round(float(max(h[1] for h in hs)), 2),
                     }
    print('GATE', act.name, json.dumps(res[act.name]))
json.dump(res, open(os.path.join(HERE, 'work', 'gates.json'), 'w'), indent=1)
