"""Staff audit per frame: staff surface vs the body mesh (excluding the right fist): nearest clearance and the number
of body vertices inside the staff's radius; staff foot height; and clip renders. Args: blend tag [clip:frames,...]."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
arm = bpy.data.objects['Mage_Rig']; mesh = bpy.data.objects['Mage']; staff = bpy.data.objects['Staff']; scene = bpy.context.scene
PARTS = json.loads(scene['pmn2_parts']); me = mesh.data
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
fist = {v for p in me.polygons if PARTS[part[p.index]] == 'HandRight' for v in p.vertices}
keep = np.array([i for i in range(len(me.vertices)) if i not in fist])
L = json.loads(scene['pmn2_staff'])['length']


def staff_profile(t):                                   # radius at fraction t from the foot (matches make_staff.py)
    z = t * L
    return 0.045 if z > L - 0.21 else (0.03 if z > L - 0.26 else 0.024)


def evaluate():
    dg = bpy.context.evaluated_depsgraph_get()
    em = mesh.evaluated_get(dg).to_mesh(); P = np.array([tuple(mesh.matrix_world @ v.co) for v in em.vertices]); mesh.evaluated_get(dg).to_mesh_clear()
    es = staff.evaluated_get(dg).to_mesh(); S = np.array([tuple(staff.matrix_world @ v.co) for v in es.vertices]); staff.evaluated_get(dg).to_mesh_clear()
    return P, S


def set_action(a):
    arm.animation_data.action = a
    if getattr(a, 'slots', None): arm.animation_data.action_slot = a.slots[0]


rest_s = np.array([tuple(v.co) for v in staff.data.vertices])
res = {}
for name in ('Idle_9', 'Walking', 'Running'):
    set_action(bpy.data.actions[name]); f0, f1 = (int(round(x)) for x in bpy.data.actions[name].frame_range)
    worst = (9, None); inside_max = 0; foot_min = 9; hit_groups = set()
    for f in range(f0, f1 + 1):
        scene.frame_set(f); P, S = evaluate()
        foot = S[np.argmin(np.linalg.norm(rest_s - rest_s[np.argmin(rest_s @ np.array(json.loads(scene['pmn2_staff'])['axis']))], axis=1))]
        # staff axis from the bone
        pb = arm.pose.bones['Staff']; g = arm.matrix_world @ pb.head; top = arm.matrix_world @ pb.tail
        ax = (top - g).normalized(); base = g - ax * (L * 0.71)
        foot_min = min(foot_min, S[:, 2].min())
        Q = P[keep]; rel = Q - np.array(base); t = rel @ np.array(ax); m = (t > 0) & (t < L)
        d = np.linalg.norm(rel[m] - np.outer(t[m], ax), axis=1)
        r = np.array([staff_profile(x / L) for x in t[m]])
        clr = d - r
        inside = int((clr < 0).sum()); inside_max = max(inside_max, inside)
        if inside:
            idx = keep[np.where(m)[0][clr < 0]]
            hit_groups.update(max(me.vertices[i].groups, key=lambda g: g.weight).group for i in idx if me.vertices[i].groups)
        if clr.size and clr.min() < worst[0]:
            worst = (float(clr.min()), f)
    res[name] = {'min_clearance_mm': round(worst[0] * 1000, 1), 'at_frame': worst[1], 'max_body_verts_inside_staff': inside_max,
                 'staff_lowest_z': round(float(foot_min), 3),
                 'hit_parts': sorted(mesh.vertex_groups[g].name for g in hit_groups)}
    print('STAFF', name, res[name])
json.dump(res, open(os.path.join(common.WORK, f'{tag}_staff_audit.json'), 'w'), indent=1)
common.workbench_clay(scene); scene.display.shading.color_type = 'SINGLE'; scene.display.shading.single_color = (0.72, 0.72, 0.7)
out = os.path.join(common.REVIEW, tag); os.makedirs(out, exist_ok=True)
for name, frames in (('Idle_9', (0,)), ('Walking', (0, 6, 12, 18)), ('Running', (0, 5, 10))):
    set_action(bpy.data.actions[name])
    for f in frames:
        scene.frame_set(f); hips = arm.matrix_world @ arm.pose.bones['mixamorig:Hips'].head
        common.render_views(os.path.join(out, f'{name}_{f:02d}'), 0.95, 2.0, views=('front', 'left', 'three_quarter'), resolution=(300, 450), target=(float(hips.x), float(hips.y)))
