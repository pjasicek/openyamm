"""Gate: the blade cuts with its edge. For each clip of the exported GLB, per frame step the tip velocity is split into
its component along the blade's edge direction and along the flat normal (both from the posed Sword bone frame of the
built mesh: edge = Sword bone local X... measured from the mesh: widest cross-section direction). Reports, over the
fastest 20 % of tip motion, the share of speed along the edge (1 = pure edge-leading cut, 0 = slapping with the flat).
Args: -- <glb>"""
import bpy, sys, math
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
me = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent is arm and 'LOD' not in o.name and 'Shadow' not in o.name)
g = me.vertex_groups['Sword']
ids = np.array([v.index for v in me.data.vertices if any(e.group == g.index for e in v.groups)])
co = np.array([tuple(v.co) for v in me.data.vertices])[ids]
sb = arm.data.bones['Sword']; h = np.array(sb.head_local); ax = np.array(sb.tail_local - sb.head_local); ax /= np.linalg.norm(ax)
t = (co - h) @ ax
blade = co[(t > 0.3) & (t < 0.6)]
perp = blade - h - np.outer((blade - h) @ ax, ax)
U = np.linalg.svd(perp - perp.mean(0), full_matrices=False)[2]
edge_rest, flat_rest = U[0], U[1]
# sign: the curved blade bows toward its spine, so the mean perpendicular offset of the mid blade points away from the
# cutting edge (a straight blade has no preferred side; the sign is then arbitrary)
if perp.mean(0) @ edge_rest > 0:
    edge_rest = -edge_rest
tip_rest = co[np.argmax(t)]
Minv = np.linalg.inv(np.array(sb.matrix_local))
loc = lambda v, w: (Minv @ np.r_[v, w])[:3]
e_l, f_l, tip_l = loc(edge_rest, 0), loc(flat_rest, 0), loc(tip_rest, 1)
for act in bpy.data.actions:
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; rows = []; prev = None
    t_ = f0
    while t_ <= f1:
        bpy.context.scene.frame_set(int(t_), subframe=t_ - int(t_))
        M = np.array(arm.matrix_world @ arm.pose.bones['Sword'].matrix)
        tip = (M @ np.r_[tip_l, 1])[:3]; e = M[:3, :3] @ e_l; f = M[:3, :3] @ f_l
        if prev is not None:
            v = tip - prev; sp = np.linalg.norm(v)
            if sp > 1e-6:
                rows.append((sp, abs(v @ e) / np.linalg.norm(e), abs(v @ f) / np.linalg.norm(f), (v @ e) / np.linalg.norm(e) / sp))
        prev = tip; t_ += 0.5
    if act.name == 'Attack' and rows:
        # at the blow (actors.yml impact, IMPACT env; default the goblin's 0.683 s): signed lead of the tip motion
        import os as _os
        imp = float(_os.environ.get('IMPACT', '0.683')) * bpy.context.scene.render.fps
        tt = [f0 + 0.5 * (i + 1) for i in range(len(rows))]
        sel_ = [r_[3] for r_, x in zip(rows, tt) if abs(x - imp) <= 0.05 * bpy.context.scene.render.fps]
        print(f'BLOW Attack signed lead at the impact {np.mean(sel_):+.2f} over {len(sel_)} samples')
    if not rows:
        continue
    r = np.array(rows); k = r[:, 0] >= np.percentile(r[:, 0], 80)
    edge_share = float((r[k, 1] / np.maximum(np.hypot(r[k, 1], r[k, 2]), 1e-9)).mean())
    # signed: + when the convex cutting edge (the curve's outer side, +edge) leads, - when the spine leads
    lead = float(np.mean(r[k, 3]))
    print(f'EDGE {act.name:9s} fastest-20% tip motion: edge-leading share {edge_share:.2f} (1 edge, 0 flat), '
          f'signed lead {lead:+.2f} (+ cutting edge first), peak speed {r[:, 0].max() * 30 / 0.5:.1f} m/s')
# roll sweep: edge direction rotated about the blade axis by phi (bone-local), attack + walk scores
import os
if os.environ.get('ROLL_SWEEP'):
    ax_l = (Minv[:3, :3] @ ax); ax_l /= np.linalg.norm(ax_l)
    for name in ('Attack', 'Walking', 'Fidget'):
        act = next(a for a in bpy.data.actions if a.name.startswith(name)); arm.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            arm.animation_data.action_slot = act.slots[0]
        f0, f1 = act.frame_range; data = []; prev = None; t_ = f0
        while t_ <= f1:
            bpy.context.scene.frame_set(int(t_), subframe=t_ - int(t_))
            M = np.array(arm.matrix_world @ arm.pose.bones['Sword'].matrix)
            tip = (M @ np.r_[tip_l, 1])[:3]
            if prev is not None:
                data.append((tip - prev, M[:3, :3].copy()))
            prev = tip; t_ += 0.5
        sp = np.array([np.linalg.norm(v) for v, _ in data]); k = sp >= np.percentile(sp, 80)
        res = []
        for phi in range(0, 180, 15):
            c_, s_ = math.cos(math.radians(phi)), math.sin(math.radians(phi))
            e2 = e_l * c_ + np.cross(ax_l, e_l) * s_; f2 = np.cross(ax_l, e2)
            vals = [abs(v @ (R @ e2)) / max(np.hypot(v @ (R @ e2), v @ (R @ f2)), 1e-9) for (v, R), kk in zip(data, k) if kk]
            res.append((phi, round(float(np.mean(vals)), 2)))
        print('SWEEP', name, res)
