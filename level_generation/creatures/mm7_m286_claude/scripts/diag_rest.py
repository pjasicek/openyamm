"""Diagnosis renders of the step1 body at rest: MODE=orig renders the pre-reshape positions ('orig_co'), MODE=cur the
current ones, MODE=disp the current mesh coloured by the reshape displacement jump between neighbouring vertices
(red = a step). Optional pose: CLIP/FRAME on a rig blend. Camera: azimuth AZ deg (0 front, 90 his left), target
CX,CY,CZ, ortho height OH, elevation EL deg. Args: -- <blend> <out png>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
body = bpy.data.objects['Body']; me = body.data
mode = os.environ.get('MODE', 'cur')
rig = bpy.data.objects.get('Rig')
clip = os.environ.get('CLIP')
if rig is not None:
    rig.animation_data_create()
    if clip:
        act = bpy.data.actions[clip]; rig.animation_data.action = act
        if len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        bpy.context.scene.frame_set(int(os.environ.get('FRAME', '0')))
    else:
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
oc = np.zeros(len(me.vertices) * 3)
if 'orig_co' in me.attributes:
    me.attributes['orig_co'].data.foreach_get('vector', oc)
oc = oc.reshape(-1, 3)
co = np.array([tuple(v.co) for v in me.vertices])
if mode == 'orig':
    for v, p in zip(me.vertices, oc):
        v.co = p
for p in me.polygons:
    p.use_smooth = True
sc = bpy.context.scene; common.workbench_clay(sc)
if mode == 'weight':                                            # vertex colour = weight of the groups in WGROUPS
    keys = os.environ.get('WGROUPS', 'B_R_UpperArm').split(',')
    gi = {g.index for g in body.vertex_groups if any(g.name.startswith(k) for k in keys)}
    wv = np.array([sum(e.weight for e in v.groups if e.group in gi) for v in me.vertices])
    col = me.color_attributes.new('w', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(col.data):
        t = float(wv[i]); c.color = (t, 0.15 + 0.5 * (1 - abs(2 * t - 1)), 1 - t, 1)
    sc.display.shading.color_type = 'VERTEX'
if mode == 'disp':
    d = co - oc
    E = np.array([tuple(e.vertices) for e in me.edges]); L = np.linalg.norm(oc[E[:, 0]] - oc[E[:, 1]], axis=1)
    jump = np.linalg.norm(d[E[:, 0]] - d[E[:, 1]], axis=1) / np.maximum(L, 1e-4)     # displacement change per metre
    vj = np.zeros(len(co)); np.maximum.at(vj, E[:, 0], jump); np.maximum.at(vj, E[:, 1], jump)
    print('DISP edges with displacement gradient > 0.3:', int((jump > 0.3).sum()), 'max', round(float(jump.max()), 3))
    col = me.color_attributes.new('disp', 'FLOAT_COLOR', 'POINT')
    t = np.clip(vj / 0.5, 0, 1)
    for i, c in enumerate(col.data):
        c.color = (0.6 + 0.4 * t[i], 0.6 * (1 - t[i]), 0.6 * (1 - t[i]), 1)
    sc.display.shading.color_type = 'VERTEX'
az, el = math.radians(float(os.environ.get('AZ', '65'))), math.radians(float(os.environ.get('EL', '8')))
tgt = Vector(tuple(float(x) for x in os.environ.get('TGT', '0.2,0,1.3').split(',')))
dist = 6.0
loc = tgt + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
cam = common.ortho_camera('c', loc, (0, 0, 0), float(os.environ.get('OH', '0.9')))
cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.resolution_x = sc.render.resolution_y = 700
sc.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
