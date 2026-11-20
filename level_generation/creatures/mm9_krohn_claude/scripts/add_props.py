"""Add Krohn's glaive and sword (work/props.npz from make_props.py, MM9 bind-pose glTF coordinates) to a rigged master as
object 'Props': moved with the fitted Xspear / Xsword joints (fit_rig.py translated the joints only, so a rigid piece
moves by its joint's translation), weighted 1.0 to Xspear (glaive) / Xsword (sword), UV layer 'UVMap' in the props atlas,
parented to the rig with an Armature modifier. build_export_v2.py joins it into the body as a third material.
Optional SPEAR_OFFSET=x,y,z / SWORD_OFFSET=x,y,z (metres, Blender) and SWORD_ROT=deg about the joint's local x (clearance
fixes found on the posed body). Args: -- <in blend> <out blend> <props npz> <fit report json>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, NPZ, FIT = a[:4]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
old = bpy.data.objects.get('Props')
if old:
    bpy.data.objects.remove(old)
d = np.load(NPZ)
v, uv, f, part = d['v'], d['uv'], d['f'], d['part']
P = np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1)              # glTF (y up) -> Blender (z up)
fit = json.load(open(FIT))
rep = {}
for k, joint, env in ((0, 'Xspear', 'SPEAR_OFFSET'), (1, 'Xsword', 'SWORD_OFFSET')):
    j0 = np.array(fit['joints_mm9'][joint])
    j1 = np.array(rig.matrix_world @ rig.data.bones[joint].head_local)
    m = part == k
    P[m] += j1 - j0
    if os.environ.get(env):
        P[m] += np.array([float(x) for x in os.environ[env].split(',')])
    rep[joint] = [round(float(x), 4) for x in (j1 - j0)]
if os.environ.get('SWORD_ROT'):
    ang = math.radians(float(os.environ['SWORD_ROT']))
    j1 = np.array(rig.matrix_world @ rig.data.bones['Xsword'].head_local)
    ax = np.array(rig.matrix_world.to_3x3() @ rig.data.bones['Xsword'].matrix_local.to_3x3() @ Vector((1, 0, 0)))
    R = np.array(Matrix.Rotation(ang, 3, Vector(ax.tolist())))
    m = part == 1
    P[m] = (P[m] - j1) @ R.T + j1
if os.environ.get('SWORD_FIT'):
    # lay the scabbard on the back: the body's outermost back surface along the sword axis (ray from +y), the axis
    # turned (about the guard) and moved so it runs SWORD_FIT metres off that surface (MM9's thin cape let the sword lie
    # 4 cm off the back; our fur cape is up to 19 cm thicker there)
    from mathutils.bvhtree import BVHTree
    clr = float(os.environ['SWORD_FIT'])
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(body, dg)
    m = part == 1
    loc = d['local'][m]
    c0 = P[m][np.argmin(np.abs(loc[:, 0] - 0.0) + np.abs(loc[:, 1]) + np.abs(loc[:, 2]))]   # near the guard centre
    # the sword axis in Blender: least squares through the vertices by their local axis-0 coordinate
    A = np.c_[loc[:, 0], np.ones(len(loc))]
    coef = np.linalg.lstsq(A, P[m], rcond=None)[0]           # P = t * dir + origin
    dirv, org = coef[0], coef[1]
    ts = np.linspace(0.05, 1.05, 11)
    ys = []
    for t in ts:
        q = org + t * dirv
        hit = bvh.ray_cast(Vector((q[0], 3.0, q[2])), Vector((0, -1, 0)))
        ys.append(hit[0].y if hit[0] is not None else q[1])
    want = np.array(ys) + clr
    fit_y = np.polyfit(ts, want, 1)                        # y = a t + b along the scabbard
    new_org = np.array([org[0], fit_y[1], org[2]]); new_dir = np.array([dirv[0], fit_y[0], dirv[2]])
    new_dir *= np.linalg.norm(dirv) / np.linalg.norm(new_dir)
    R = np.array(Vector(dirv.tolist()).rotation_difference(Vector(new_dir.tolist())).to_matrix())
    P[m] = (P[m] - org) @ R.T + new_org
    rep['sword_fit'] = {'surface_y': [round(float(y), 3) for y in ys], 'moved_origin_m': [round(float(x), 3) for x in new_org - org],
                        'turn_deg': round(float(np.degrees(np.arccos(np.clip(dirv @ new_dir / (dirv @ dirv), -1, 1)))), 2)}
me = bpy.data.meshes.new('Props')
me.from_pydata(P.tolist(), [], f.tolist())
me.update()
ul = me.uv_layers.new(name='UVMap')
for poly in me.polygons:
    for li in poly.loop_indices:
        ul.data[li].uv = tuple(uv[me.loops[li].vertex_index])
ob = bpy.data.objects.new('Props', me)
bpy.context.scene.collection.objects.link(ob)
ob.parent = rig
ob.matrix_parent_inverse = rig.matrix_world.inverted()
# SWORD_BONE: the bone that carries the sword (MM9: Xsword on Spine3; mm9_krohn test: the cape's centre pivot, so the
# scabbard rides on the cape the way it lies on it)
for k, joint in ((0, 'Xspear'), (1, os.environ.get('SWORD_BONE', 'Xsword'))):
    g = ob.vertex_groups.new(name=joint)
    g.add([int(i) for i in np.nonzero(part == k)[0]], 1.0, 'REPLACE')
mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
for p in me.polygons:
    p.use_smooth = True
# hard edges on the blade bevel and the plate outline: split normals by angle at export (auto smooth via edge sharp)
bm = bmesh.new(); bm.from_mesh(me)
for e in bm.edges:
    if len(e.link_faces) == 2 and e.link_faces[0].normal.angle(e.link_faces[1].normal) > math.radians(40):
        e.smooth = False
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('PROPS', json.dumps({'moves_m': rep, 'tris': len(me.polygons)}))
