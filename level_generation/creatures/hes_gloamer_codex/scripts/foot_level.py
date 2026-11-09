"""Level the feet while grounded (playbook: retargeted clips carry the source body's foot posture; review 1: the Mixamo
idle pitched both feet ~20 deg toe-up, so the toes hovered 4-6 cm and the feet looked warped and unplanted, and the
attack inherited Standing's feet). Per clip, frame and foot: the heel and toe-tip reference vertices (rest: the
rearmost and frontmost sole vertices, both on the floor) are measured on the skinned mesh; the Foot bone turns about the
ankle's lateral axis by the pitch that puts them level again, weighted by groundedness (1 with the heel or toe below
2 cm, 0 above 8 cm); the toes take the rest relation. Then the foot is moved down/up by IK-free means: the pelvis is
not touched; a later floor pass handles height. Args: -- <in blend> <out blend> <Action> ..."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
vg = [g.name for g in body.vertex_groups]
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
REF = {}
for sd in 'LR':
    m = np.array([sum(e.weight for e in v.groups if vg[e.group] in (f'B_{sd}_Foot', f'B_{sd}_Toe0')) > 0.5 for v in me.vertices])
    idx = np.where(m & (rest[:, 2] < 0.012))[0]
    heel = idx[np.argmax(rest[idx, 1])]; toe = idx[np.argmin(rest[idx, 1])]
    REF[sd] = (heel, toe)
    print('FOOTLEVEL ref', sd, 'heel', np.round(rest[heel], 3), 'toe', np.round(rest[toe], 3))


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and len(x.slots): rig.animation_data.action_slot = x.slots[0]


def mesh_z():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear(); return P


for item in acts:
    # <Action>[:const][:until=<frame>]  const = only the clip's constant tilt (median grounded pitch per foot; keeps the
    # walk's heel strike and toe-off), until = level only up to that frame (the death before he lies down)
    parts = item.split(':'); an = parts[0]; const = 'const' in parts
    until = next((int(x.split('=')[1]) for x in parts if x.startswith('until=')), None)
    act = bpy.data.actions[an]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); worst = 0.0
    off = {}
    if const:
        pit = {'L': [], 'R': []}
        for f in range(f0, f1 + 1):
            set_act(act); sc.frame_set(f); P = mesh_z()
            for sd in 'LR':
                hv, tv = REF[sd]; h, t = Vector(P[hv]), Vector(P[tv])
                if min(h.z, t.z) < 0.015:
                    d = t - h; pit[sd].append(math.atan2(d.z, math.hypot(d.x, d.y)))
        off = {sd: float(np.median(pit[sd])) if pit[sd] else 0.0 for sd in 'LR'}
        print('FOOTLEVEL', an, 'constant tilt deg', {k: round(math.degrees(v), 1) for k, v in off.items()})
    keys = []
    for f in range(f0, f1 + 1):
        set_act(act); sc.frame_set(f)
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        set_act(None)
        for pb in rig.pose.bones: pb.matrix_basis = snap[pb.name]
        if not const:
            for sd in 'LR': rig.pose.bones[f'B_{sd}_Toe0'].matrix_basis = Matrix()
        bpy.context.view_layer.update()
        for it in range(1 if const else 2):
            P = mesh_z()
            for sd in 'LR':
                hv, tv = REF[sd]; h, t = Vector(P[hv]), Vector(P[tv])
                g = 1.0 if const else float(np.clip((0.08 - min(h.z, t.z)) / 0.06, 0, 1))
                if until is not None and f > until:
                    g *= float(np.clip(1 - (f - until) / 6.0, 0, 1))
                if g <= 0: continue
                d = t - h; horiz = math.hypot(d.x, d.y)
                pitch = off[sd] if const else math.atan2(d.z, horiz)    # + = toe up
                lat = Vector((d.y, -d.x, 0)).normalized()          # right-hand lateral axis of the heel -> toe line
                M = armik.W(rig, f'B_{sd}_Foot'); tr = M.translation.copy()
                R = Matrix.Rotation(-pitch * g, 4, lat)
                # sign check: rotating about lat by +x lifts the toe if lat x d points up
                if (lat.cross(d)).z < 0: R = Matrix.Rotation(pitch * g, 4, lat)
                M = R @ M; M.translation = tr; armik.set_world(rig, f'B_{sd}_Foot', M)
                if it == 0: worst = max(worst, abs(math.degrees(pitch)) * g)
        keys.append({n: rig.pose.bones[n].rotation_quaternion.copy() for n in ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0')})
    set_act(act)
    for i, f in enumerate(range(f0, f1 + 1)):
        for n, q in keys[i].items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)
    print(f'FOOTLEVEL {an}: max grounded sole pitch corrected {worst:.1f} deg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
