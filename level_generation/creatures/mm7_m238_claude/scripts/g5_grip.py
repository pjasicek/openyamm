"""G5 grip check at one action frame: the derived grip (work/grip_source.json, source hand-local) is placed on our right
hand (hand world rotation = source's; position scaled by the measured hand-length ratio). Measures, for the posed
right-hand skin: distance of each finger's skin (by finger label) to the handle axis within the handle span
(min / 10th percentile) and the palm's distance; reports the largest handle radius that no finger skin enters.
Renders the posed hand (body cut to the hand) with a handle cylinder of that radius from four sides.
Args: -- <blend> <action> <frame> <out prefix>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, action, frame, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(frame))
g = json.load(open(os.path.join(HERE, 'work', 'grip_source.json')))
SRC = json.load(open(os.path.join(HERE, 'work', 'source_rest.json')))
# measured hand lengths (build_rig HAND line): ours / source
k = 0.151 / 0.363
hm = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
loc, rot, _ = hm.decompose(); R = rot.to_matrix()
c_src = loc + R @ (Vector(g['centre_hand']) * 0.01 * k)
ax_src = (R @ Vector(g['axis_hand'])).normalized()
# our own grip: circle through each posed finger's three joint heads (index..pinky), centres -> handle axis
def circle(pts):
    cc = pts.mean(0); vt = np.linalg.svd(pts - cc, full_matrices=False)[2]; e1, e2 = vt[0], vt[1]
    xy = np.stack([(pts - cc) @ e1, (pts - cc) @ e2], 1)
    sol = np.linalg.lstsq(np.column_stack([2 * xy, np.ones(len(xy))]), (xy ** 2).sum(1), rcond=None)[0]
    return cc + sol[0] * e1 + sol[1] * e2, math.sqrt(sol[2] + sol[0] ** 2 + sol[1] ** 2)
cents, radii = [], []
for i in (1, 2, 3, 4):
    names = [f'B_R_Finger{i}', f'B_R_Finger{i}1', f'B_R_Finger{i}2']
    pts = np.array([tuple(rig.matrix_world @ rig.pose.bones[n].head) for n in names])
    cc, r = circle(pts); cents.append(cc); radii.append(r)
cents = np.array(cents); m0 = cents.mean(0); a0 = np.linalg.svd(cents - m0, full_matrices=False)[2][0]
if a0 @ np.array(ax_src) < 0:
    a0 = -a0
off = np.linalg.norm((cents - m0) - np.outer((cents - m0) @ a0, a0), axis=1)
c, ax = Vector(m0), Vector(a0).normalized()
print('OURGRIP centres off-axis cm', np.round(off * 100, 2), 'curl radii cm', np.round(np.array(radii) * 100, 2),
      '| vs source-derived: axis angle deg', round(math.degrees(ax.angle(ax_src)), 1), 'centre offset cm',
      round((c - c_src).length * 100, 2))
# store the grip in our hand bone's local space for the sword attachment
inv = (rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix).inverted()
json.dump({'centre_hand_local': list(inv @ c), 'axis_hand_local': list((inv.to_3x3() @ ax).normalized()), 'action': action,
           'frame': int(frame)}, open(os.path.join(HERE, 'work', 'grip_ours.json'), 'w'), indent=1)
deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
lab = np.zeros(len(P), np.int32); me.attributes['finger'].data.foreach_get('value', lab)
C, A = np.array(c), np.array(ax)
v = P - C; along = v @ A; rad = np.linalg.norm(v - np.outer(along, A), axis=1)
near = np.abs(along) < 0.05
names = ['hand', 'thumb', 'index', 'middle', 'ring', 'pinky']
hw = body.vertex_groups['B_R_Hand'].index
right = P[:, 0] < 0
rep = {}
for f in range(6):
    msk = near & right & (lab == f) & (np.linalg.norm(P - C, axis=1) < 0.08)
    if msk.any():
        rep[names[f]] = (round(float(rad[msk].min()) * 100, 2), round(float(np.percentile(rad[msk], 10)) * 100, 2), int(msk.sum()))
safe = min(v[0] for v in rep.values()) / 100
print('GRIP', action, frame, 'skin->handle-axis min/p10 cm (count):', rep, '| largest clear handle radius cm', round(safe * 100, 2))
# render: cut the posed body to the hand region and add a handle
bm = bmesh.new(); bm.from_mesh(m) if False else None
mesh_copy = bpy.data.meshes.new('posed'); bm2 = bmesh.new()
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); bm2.from_mesh(ev.to_mesh()); ev.to_mesh_clear()
bm2.transform(body.matrix_world)
bmesh.ops.delete(bm2, geom=[x for x in bm2.verts if (x.co - c).length > 0.12], context='VERTS')
bm2.to_mesh(mesh_copy); bm2.free()
o = bpy.data.objects.new('posedhand', mesh_copy); bpy.context.scene.collection.objects.link(o)
body.hide_render = True
for x in bpy.data.objects:
    if x.type == 'MESH' and x not in (o,):
        x.hide_render = True
hm_ = bpy.data.meshes.new('h'); hb = bmesh.new()
bmesh.ops.create_cone(hb, cap_ends=True, segments=16, radius1=max(safe, 0.004), radius2=max(safe, 0.004), depth=0.16)
hb.to_mesh(hm_); hb.free()
ho = bpy.data.objects.new('handle', hm_); bpy.context.scene.collection.objects.link(ho)
ho.location = c; ho.rotation_mode = 'QUATERNION'; ho.rotation_quaternion = ax.to_track_quat('Z', 'Y')
mat = bpy.data.materials.new('hm'); mat.diffuse_color = (0.75, 0.45, 0.2, 1); hm_.materials.append(mat)
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
for vname in ('front', 'left', 'back', 'right'):
    common.render_views(f'{out}_{vname}', c.z, 0.2, views=(vname,), resolution=(360, 360), target=(c.x, c.y))
