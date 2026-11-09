"""Frame-by-frame hand/wrist/forearm deformation audit of one clip (default Attack) on work/rig_v7.blend.

For every frame and side: skin edge-length ratios (deformed / rest) and triangle-area ratios on four zones picked by
dominant bone and rest position: Hand (fist), Wrist (forearm skin within 6 cm of the wrist joint), ForeArm (rest of
the forearm), Elbow (skin within 6 cm of the elbow joint). Reports the extremes (min/max ratio, flipped triangles) and
the wrist swing / forearm twist / upper-arm roll of the pose. Renders close-ups of each hand per frame (camera follows
the hand: front-ish and side-ish to the forearm) into review/hand_audit/<clip>/.
Usage: blender --background --python hand_audit.py -- [clip] [render 0/1]"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CLIP = args[0] if args else 'Attack'
RENDER = len(args) < 2 or args[1] == '1'
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v7.blend'))
import gua_rig as gr
arm, mesh, AW = gr.arm, gr.mesh, gr.AW
me = mesh.data
dom = np.array([d or '' for d in gr._dom])
rest = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
me.calc_loop_triangles()
tris = np.array([tuple(t.vertices) for t in me.loop_triangles])
edges = np.array([tuple(e.vertices) for e in me.edges])


def zones(side):
    w = np.array(AW @ arm.data.bones[side + 'Hand'].head_local)
    e = np.array(AW @ arm.data.bones[side + 'ForeArm'].head_local)
    d_w = np.linalg.norm(rest - w, axis=1)
    d_e = np.linalg.norm(rest - e, axis=1)
    hand = dom == side + 'Hand'
    fore = np.isin(dom, [side + 'ForeArm', side + 'ForeArmTwist1', side + 'ForeArmTwist2'])
    upper = dom == side + 'Arm'
    return {'Hand': hand,
            'Wrist': (fore | hand) & (d_w < 0.06) & ~hand,
            'ForeArm': fore & (d_w >= 0.06) & (d_e >= 0.06),
            'Elbow': (fore | upper) & (d_e < 0.06)}


Z = {s: zones(s) for s in ('Left', 'Right')}
rest_len = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
rest_cross = np.cross(rest[tris[:, 1]] - rest[tris[:, 0]], rest[tris[:, 2]] - rest[tris[:, 0]])
rest_area = np.linalg.norm(rest_cross, axis=1) / 2
Y = Vector((0, 1, 0))


def rel(child, parent):
    q = ((AW @ gr.B(parent).matrix).to_3x3().normalized().inverted() @
         (AW @ gr.B(child).matrix).to_3x3().normalized()).to_quaternion()
    qr = (gr.rest3(parent).inverted() @ gr.rest3(child)).to_quaternion()
    return gr.swing_twist_deg(qr.inverted() @ q, Y)


act, (f0, f1) = gr.set_action(CLIP)
out = os.path.join(common.REVIEW, 'hand_audit', CLIP)
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
if RENDER:
    common.workbench_clay(sc)
    sc.display.shading.color_type = 'SINGLE'
    mesh.show_wire = True
rows = []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    em = mesh.evaluated_get(dg).to_mesh()
    P = np.array([tuple(mesh.matrix_world @ v.co) for v in em.vertices])
    mesh.evaluated_get(dg).to_mesh_clear()
    ln = np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1) / np.maximum(rest_len, 1e-6)
    cr = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    area = np.linalg.norm(cr, axis=1) / 2 / np.maximum(rest_area, 1e-9)
    flip = (cr * rest_cross).sum(1) < 0
    row = {'f': f}
    for s, zs in Z.items():
        for zn, m in zs.items():
            em_ = m[edges].all(1)
            tm = m[tris].all(1)
            if not em_.any():
                continue
            row[f'{s[0]}_{zn}'] = (round(float(ln[em_].min()), 2), round(float(ln[em_].max()), 2),
                                   round(float(area[tm].min()), 2) if tm.any() else None, int(flip[tm].sum()))
        sw, tw = rel(s + 'Hand', s + 'ForeArm')
        row[f'{s[0]}_wrist'] = (round(sw), round(tw))
        row[f'{s[0]}_ftwist'] = round(rel(s + 'ForeArm', s + 'Arm')[1])
        row[f'{s[0]}_roll'] = round(rel(s + 'Arm', s + 'Shoulder')[1])
    rows.append(row)
    if RENDER:
        for s in ('Left', 'Right'):
            h = AW @ gr.B(s + 'Hand').head
            e = AW @ gr.B(s + 'ForeArm').head
            c = h + (h - e) * 0.15
            fa = (h - e).normalized()
            side = fa.cross(Vector((0, 0, 1)))
            if side.length < 0.2:
                side = fa.cross(Vector((0, 1, 0)))
            side.normalize()
            up = side.cross(fa).normalized()
            for tag, d in (('a', side), ('b', up)):
                cam = common.ortho_camera('c', c + d * 2.0, (0, 0, 0), 0.34)
                cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                sc.camera = cam
                sc.render.resolution_x = sc.render.resolution_y = 260
                sc.render.filepath = os.path.join(out, f'{s[0]}_{f:02d}_{tag}.png')
                bpy.ops.render.render(write_still=True)
                bpy.data.objects.remove(cam, do_unlink=True)
json.dump(rows, open(os.path.join(common.WORK, f'hand_audit_{CLIP}.json'), 'w'), indent=0)
for r in rows:
    print('HA', json.dumps(r))
