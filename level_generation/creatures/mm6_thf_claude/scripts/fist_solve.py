"""Fist around a dagger grip for each hand (work/rig_v1.blend in place, after finger_rig.py).

Grip axis: along the hand's knuckle axis k, through the palm crease (s = sk + GRIP_S along a), GRIP_R + the palm
surface offset toward the palm normal n. Curl: knuckle angle A and middle angle B (tip = 0.7 B) about each finger bone's
local X, fitted so the finger joints lie on a circle of grip radius + half a finger around the grip axis. Thumb: Euler angles (local X, Y, Z) bringing its tip over the top
(wrist side) of the grip, beyond its far side, closing the fist. Stores scene['thf_fist'] = {S: {fing: [A, B, 0.7B], thumb: [x, y, z, x2],
grip: point, axis}} (degrees). Renders review/fist_*.png."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data; scene = bpy.context.scene
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity(); b.rotation_mode = 'QUATERNION'
bpy.context.view_layer.update()
H = json.loads(scene['thf_hands'])
GRIP_R, GRIP_S = 0.0105, 0.004
PARTS = json.loads(scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
hi = PARTS.index('Hand')
gname = {g.index: g.name for g in mesh.vertex_groups}


def evaluated(ids):
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(mesh.matrix_world @ m.vertices[i].co) for i in ids]); ev.to_mesh_clear()
    return P


def set_curl(names, degs, axis='X'):
    for n_, d in zip(names, degs):
        pb = arm.pose.bones[n_]
        pb.rotation_quaternion = Quaternion(Vector((1, 0, 0)) if axis == 'X' else Vector((0, 0, 1)), math.radians(d))
    bpy.context.view_layer.update()


out = {}
for S, h in H.items():
    side = h['side']; a = Vector(h['a']); n = Vector(h['n']); k = Vector(h['k']); c = Vector(h['c'])
    vid = [v.index for v in me.vertices if any(gname[g.group].startswith(('Fing' + S, 'Thumb' + S)) for g in v.groups)]
    hand = sorted({v for p in me.polygons if part[p.index] == hi for v in p.vertices
                   if (mesh.matrix_world @ me.vertices[v].co).x * (1 if S == 'L' else -1) > 0})
    P0 = np.array([tuple(mesh.matrix_world @ me.vertices[i].co) for i in hand])
    s = (P0 - np.array(c)) @ np.array(a); off = (P0 - np.array(c)) @ np.array(n)
    band = (s > h['sk'] - 0.02) & (s < h['sk'] + 0.004)
    palm = float(np.percentile(off[band], 95))
    G = c + a * (h['sk'] + GRIP_S) + n * (palm + GRIP_R)
    fid = [v for v in vid if any(gname[g.group].startswith('Fing' + S) for g in me.vertices[v].groups)]
    tid = [v for v in vid if any(gname[g.group].startswith('Thumb' + S) for g in me.vertices[v].groups)]
    fn = [f'Fing{S}{j}' for j in (1, 2, 3)]; tn = [f'Thumb{S}{j}' for j in (1, 2)]

    def radial(P):
        d = P - np.array(G); t = d @ np.array(k)
        return np.linalg.norm(d - np.outer(t, np.array(k)), axis=1), t
    # sign of a curl: +X must move the fingertips toward the palm side (+n)
    set_curl(fn, [0, 0, 0]); base = evaluated(fid).mean(0)
    set_curl(fn, [30, 0, 0]); moved = evaluated(fid).mean(0)
    sign = 1 if (moved - base) @ np.array(n) > 0 else -1
    # analytic wrap: finger joints on a circle of radius RHO around the grip G (grip + half the finger thickness)
    RHO = GRIP_R + 0.0085
    G = c + a * (h['sk'] + GRIP_S) + n * (palm + GRIP_R)
    K = Vector(h['fing'][0][0]); segs = [(Vector(p1) - Vector(p0)) for p0, p1 in h['fing']]
    bx = (arm.matrix_world.to_3x3() @ arm.data.bones[fn[0]].matrix_local.to_3x3()) @ Vector((1, 0, 0))
    ax = bx.normalized() * sign                           # the bone's own X axis (pose rotations are about it)
    best = (1e9, None)
    for A in range(20, 121, 2):
        for B in range(20, 121, 2):
            C = 0.7 * B; P = K.copy(); err = 0.0; ang = 0.0
            for d, t in zip(segs, (A, B, C)):
                ang += t
                P = P + Matrix.Rotation(math.radians(ang), 3, ax) @ d
                err += ((P - G).length - RHO) ** 2
            if err < best[0]:
                best = (err, (A, B))
    A, B = best[1]
    set_curl(fn, [sign * A, sign * B, sign * 0.7 * B])
    r, t = radial(evaluated(fid))
    inside = int(((r < GRIP_R - 0.001) & (np.abs(t) < 0.03)).sum())
    # thumb: closes the fist over the grip
    P = K.copy(); ang = 0.0; joints = []
    for d, t_ in zip(segs, (A, B, 0.7 * B)):
        ang += t_; P = P + Matrix.Rotation(math.radians(ang), 3, ax) @ d; joints.append(P.copy())
    # the fingers wrap the grip from below (fingertip side) back up toward the palm; the open side of the fist is the
    # top of the grip (wrist side), so the thumb tip lies over the top of the grip, just beyond its far side
    target = np.array(G - a * (GRIP_R + 0.007) + n * 0.006)
    set_curl(tn, [0, 0]); T0 = evaluated(tid); tbase0 = np.array(h['thumb_base'])
    tip_i = int(np.argmax(np.linalg.norm(T0 - tbase0, axis=1)))       # the thumb's tip vertex
    tbest = (1e9, None)
    for tx in range(-130, 31, 10):
        for ty in range(-60, 61, 15):
            for tz in range(-70, 71, 10):
                pb = arm.pose.bones[tn[0]]
                pb.rotation_quaternion = Euler((math.radians(tx), math.radians(ty), math.radians(tz))).to_quaternion()
                arm.pose.bones[tn[1]].rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(0.5 * tx))
                bpy.context.view_layer.update()
                T = evaluated(tid); r, t = radial(T)
                pen = int((r < GRIP_R - 0.001).sum())
                tipd = float(np.linalg.norm(T[tip_i] - target))
                score = tipd + 0.004 * pen
                if score < tbest[0]:
                    tbest = (score, (tx, ty, tz, pen, tipd))
    tx, ty, tz, pen, tipd = tbest[1]
    out[S] = {'fing': [sign * A, sign * B, sign * 0.7 * B], 'thumb': [tx, ty, tz, 0.5 * tx], 'grip': list(G), 'axis': list(k),
              'width_axis': list(a), 'flat': list(n), 'palm_off': palm}
    print('FIST', S, 'curl', out[S]['fing'], 'fit rms mm %.1f' % (math.sqrt(best[0] / 3) * 1000), 'finger verts inside grip', inside, '| thumb', (tx, ty, tz), 'pen', pen,
          'tip-target %.1f mm' % (tipd * 1000))
scene['thf_fist'] = json.dumps(out)
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
# render the fists (pose applied, hands only, grip cylinder shown)
for S, f in out.items():
    set_curl([f'Fing{S}{j}' for j in (1, 2, 3)], f['fing'])
    pb = arm.pose.bones[f'Thumb{S}1']
    pb.rotation_quaternion = Euler(tuple(math.radians(x) for x in f['thumb'][:3])).to_quaternion()
    arm.pose.bones[f'Thumb{S}2'].rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(f['thumb'][3]))
bpy.context.view_layer.update()
for S, f in out.items():
    bpy.ops.mesh.primitive_cylinder_add(radius=GRIP_R, depth=0.10, location=f['grip'])
    cyl = bpy.context.active_object
    cyl.rotation_euler = Vector(f['axis']).to_track_quat('Z', 'Y').to_euler()
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); pl = bm.faces.layers.int['part']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[pl] != hi], context='FACES'); bm.to_mesh(me); bm.free()
sc = scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
for S, h in H.items():
    c = Vector(out[S]['grip']); n = Vector(h['n']); k = Vector(h['k'])
    for nm, d in (('palm', -n), ('thumb', k), ('back', n), ('end', Vector(h['a']))):
        cam = common.ortho_camera('c', c - d * 1.0, (0, 0, 0), 0.14)
        cam.rotation_euler = (d.to_track_quat('-Z', 'Y' if abs(d.z) < 0.9 else 'X')).to_euler()
        sc.camera = cam; sc.render.resolution_x = sc.render.resolution_y = 360
        sc.render.filepath = os.path.join(common.REVIEW, f'fist_{S}_{nm}.png'); bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)
