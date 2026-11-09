"""G5: solve a right-hand fist around a fixed handle, for OUR fingers (the source's tight curl leaves no room for a
handle inside our thicker fingers; scaling it did not work - TEST_DRIVE.md).
Handle: direction = the grip axis derived from the source curl (circle centres of our posed fingers at the source
grip, `action`/`frame`); position = that line moved along the palm normal until the palm skin clears R_HANDLE.
Fingers (index..pinky): from OUR rest finger pose (relative to the posed hand), each finger curls about one flex axis
(finger direction x palm normal) with three angles found by grid search, so that sample points along each phalanx
sit at R_HANDLE + the finger's measured half-thickness from the handle axis, never inside. The thumb closes over the
handle (one swing across the palm + flex of its two outer joints). Result: per-finger local rotations relative to the
hand in work/grip_pose.json and the handle in hand-local space; applied as a constant pose in every clip by
apply_grip.py. Args: -- <blend> <action> <frame>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
blend, action, frame = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_HANDLE = .0088      # goblin hand ~0.21 m at the 1.7 m working scale (bar1 0.012)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
W = rig.matrix_world
lab = np.zeros(len(me.vertices), np.int32); me.attributes['finger'].data.foreach_get('value', lab)
FING = (1, 2, 3, 4)
CH = {i: [f'B_R_Finger{i}', f'B_R_Finger{i}1', f'B_R_Finger{i}2'] for i in FING}
CH[0] = ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
FJ = json.load(open(os.path.join(HERE, 'work', 'finger_joints.json')))['R']
rest_co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
# finger half-thickness from the rest mesh: median distance of its skin to its chain
half = {}
for i, ch in CH.items():
    pts = [np.array(rig.data.bones[n].head_local) for n in ch] + [np.array(FJ[ch[-1] + '_tip'])]
    sk = rest_co[(lab == i + 1) & (rest_co[:, 0] < 0)]          # right hand only (labels cover both)
    d = np.min([np.linalg.norm(np.cross(sk - a, (b - a) / np.linalg.norm(b - a)), axis=1) for a, b in zip(pts[:-1], pts[1:])], axis=0)
    half[i] = float(np.median(d))
# posed hand at the grip frame
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(float(frame)),subframe=float(frame)%1)
src_pose = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}


def circle(pts):
    cc = pts.mean(0); vt = np.linalg.svd(pts - cc)[2]; e1, e2 = vt[0], vt[1]
    xy = np.stack([(pts - cc) @ e1, (pts - cc) @ e2], 1)
    sol = np.linalg.lstsq(np.column_stack([2 * xy, np.ones(len(xy))]), (xy ** 2).sum(1), rcond=None)[0]
    return cc + sol[0] * e1 + sol[1] * e2


cents = np.array([circle(np.array([tuple(W @ rig.pose.bones[n].head) for n in CH[i]])) for i in FING])
m0 = cents.mean(0)
# handle DIRECTION = the source's own grip axis (grip_from_source.py, source hand-local). Our hand bone rotates exactly
# like the source hand (world copy), so this axis points the blade wherever the animator's sword pointed. (An axis
# from our own posed fingers was 29 deg off and drove the blade into the legs - TEST_DRIVE.md.)
gsrc = json.load(open(os.path.join(HERE, 'work', 'grip_source.json')))
Hp = W @ rig.pose.bones['B_R_Hand'].matrix
KnifeMatrix=W@rig.pose.bones['Knife'].matrix
fixed_center=np.array(KnifeMatrix.translation);fixed_axis=np.array((KnifeMatrix.to_3x3()@Vector((0,0,1))).normalized())
A = np.array((Hp.to_3x3().normalized() @ Vector(gsrc['axis_hand'])).normalized())
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.matrix_basis = src_pose[pb.name]
for ch in CH.values():                                            # fingers back to OUR rest relative to the hand
    for n in ch:
        rig.pose.bones[n].matrix_basis = Matrix()
bpy.context.view_layer.update()
H = W @ rig.pose.bones['B_R_Hand'].matrix
# Fit this model's knuckle line; its measured hand proportions differ from the source.
knuckles=np.array([tuple(W@rig.pose.bones[CH[i][0]].head)for i in FING])
A=np.linalg.svd(knuckles-knuckles.mean(0))[2][0]
if (knuckles[0]-knuckles[-1])@A<0:A=-A
wr = np.array(H.translation)
kn = np.mean([np.array(W @ rig.pose.bones[CH[i][0]].head) for i in FING], axis=0)
fdir = kn - wr; fdir /= np.linalg.norm(fdir)
# palm normal: perpendicular to the handle and the finger direction, on the side where the rest fingertips curl
nrm = np.cross(A, fdir); nrm /= np.linalg.norm(nrm)
tips = np.mean([np.array(W @ rig.pose.bones[CH[i][-1]].head) for i in FING], axis=0)
if (tips - kn) @ nrm < 0:
    nrm = -nrm
# the handle sits in front of the palm at the finger bases (the source line through the curl centres is only a
# direction: its curl centres came from the source's over-tight fingers)
C0 = kn - fdir * 0.015
m0 = C0


def posed():
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return (np.array(body.matrix_world) @ np.c_[c.reshape(-1, 3), np.ones(len(lab))].T).T[:, :3]


def radial(P, C):
    v = P - C; return np.linalg.norm(v - np.outer(v @ A, A), axis=1), v @ A


# handle against the palm: slide the line along the palm normal until the palm skin (label 0, near) clears it
P = posed()
palm = (lab == 0) & (np.linalg.norm(P - kn, axis=1) < 0.06) & (rest_co[:, 0] < 0)
C = fixed_center.copy(); A=fixed_axis.copy()
for step in range(0):
    r, al = radial(P[palm], C)
    near = np.abs(al) < 0.04
    if not near.any() or r[near].min() >= R_HANDLE:
        break
    C = C + nrm * 0.001
print('HANDLE kept fixed; movement mm', 0, 'mm; finger half-thickness cm', {i: round(v * 100, 2) for i, v in half.items()})


def joints(i):
    pts = [np.array(W @ rig.pose.bones[n].head) for n in CH[i]]
    tail = np.array(W @ rig.pose.bones[CH[i][-1]].matrix @ rig.pose.bones[CH[i][-1]].bone.matrix_local.inverted() @ Vector(FJ[CH[i][-1] + '_tip']))
    return pts + [tail]


def fk(js, ax, angs):
    p = [j.copy() for j in js]
    for k, a in enumerate(angs):
        R = np.array(Matrix.Rotation(a, 3, Vector(ax)))
        for m in range(k + 1, len(p)):
            p[m] = p[k] + R @ (p[m] - p[k])
    return p


def cost(p, want):
    c = 0.0
    for a, b in zip(p[:-1], p[1:]):
        for t in (0.2, 0.5, 0.8, 1.0):
            q = a + (b - a) * t
            v = q - C; r = np.linalg.norm(v - A * (v @ A))
            c += (r - want) ** 2 + (400 * (want - r) ** 2 if r < want - 0.001 else 0.0)
    return c


def turn(n, ax, ang):
    pb = rig.pose.bones[n]; bpy.context.view_layer.update()
    m = W @ pb.matrix; h = m.translation.copy()
    pb.matrix = W.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(ang, 4, Vector(ax)) @ Matrix.Translation(-h) @ m)
    bpy.context.view_layer.update()


angles={1:[85,80,45],2:[60,75,25],3:[65,50,40],4:[65,80,30]};report={};shifts={}
for i in FING:
 js=joints(i);d=js[1]-js[0];spread=min(np.radians(np.arange(-60,61)),key=lambda a:(round(abs((np.array(Matrix.Rotation(a,3,Vector(nrm)))@d)@A)/np.linalg.norm(d),2),abs(a)));turn(CH[i][0],nrm,spread);js=joints(i);d=js[1]-js[0];ax=A.copy()
 if (np.array(Matrix.Rotation(.3,3,Vector(ax)))@d)@nrm<d@nrm:ax=-ax
 # Match each phalanx to the handle-normal plane; the generated rest fingers bend out of that plane.
 for joint in [1,2]:
  js2=joints(i);direction=Vector(js2[joint+1]-js2[joint]);target=direction-Vector(A)*direction.dot(Vector(A));q=direction.rotation_difference(target);axis,angle=q.to_axis_angle();turn(CH[i][joint],axis,angle)
 for name,angle in zip(CH[i],angles[i]):turn(name,ax,math.radians(angle))
 report[i]=angles[i]
previous=json.load(open(os.path.join(HERE,'work/grip_closed.json')))
for name in CH[0]:rig.pose.bones[name].rotation_quaternion=Quaternion(previous['finger_local'][name])
bpy.context.view_layer.update()
for i in range(5):
 ids=np.flatnonzero((lab==i+1)&(rest_co[:,0]<0));pos=posed()[ids];groups={body.vertex_groups[name].index for name in CH[i]};w=np.array([sum(g.weight for g in me.vertices[int(vi)].groups if g.group in groups)for vi in ids]);choices=[]
 for x in np.linspace(-.012,.012,49):
  for y in np.linspace(-.012,.012,49):
   delta=nrm*x+fdir*y;rr,along=radial(pos+w[:,None]*delta,C);rr=rr[abs(along)<.05]
   costval=10000*np.square(np.minimum(rr-.0092,0)).sum()+.1*delta@delta+3*(rr.min()-.0094)**2;choices.append((costval,delta,rr.min()))
 _,delta,minimum=min(choices,key=lambda x:x[0]);pb=rig.pose.bones[CH[i][0]];m=W@pb.matrix;m.translation+=Vector(delta);pb.matrix=W.inverted()@m;bpy.context.view_layer.update();shifts[i]={'world_mm':(delta*1000).tolist(),'minimum_radius_mm':minimum*1000,'base_location':list(pb.location)}
actual=posed();clear={i:float(radial(actual[(lab==i+1)&(rest_co[:,0]<0)],C)[0].min())*1000 for i in range(5)}
FL={name:list(rig.pose.bones[name].rotation_quaternion)for ch in CH.values()for name in ch};locations={name:list(rig.pose.bones[name].location)for ch in CH.values()for name in ch};inv=(W@rig.pose.bones['B_R_Hand'].matrix).inverted()
json.dump({'finger_local':FL,'finger_locations':locations,'radius':R_HANDLE,'curl_deg':report,'minimum_skin_radius_mm':clear,'metacarpal_fit':shifts},open(os.path.join(HERE,'work/grip_final.json'),'w'),indent=2);print('GRIP_FINAL',clear,shifts,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'work/grip_final_preview.blend'))
# ---------------------------------------------------------------- review renders (posed hand cut + handle)
if os.environ.get('GRIP_RENDER'):
    import bmesh
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import common
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); bm2 = bmesh.new(); bm2.from_mesh(ev.to_mesh()); ev.to_mesh_clear()
    bm2.transform(body.matrix_world)
    bmesh.ops.delete(bm2, geom=[x for x in bm2.verts if (x.co - Vector(C)).length > 0.12], context='VERTS')
    mc = bpy.data.meshes.new('posed'); bm2.to_mesh(mc); bm2.free()
    o = bpy.data.objects.new('posedhand', mc); bpy.context.scene.collection.objects.link(o)
    for x in bpy.data.objects:
        if x.type == 'MESH' and x is not o:
            x.hide_render = True
    hb = bmesh.new(); bmesh.ops.create_cone(hb, cap_ends=True, segments=16, radius1=R_HANDLE, radius2=R_HANDLE, depth=0.16)
    hm_ = bpy.data.meshes.new('h'); hb.to_mesh(hm_); hb.free()
    ho = bpy.data.objects.new('handle', hm_); bpy.context.scene.collection.objects.link(ho)
    ho.location = Vector(C); ho.rotation_mode = 'QUATERNION'; ho.rotation_quaternion = Vector(A).to_track_quat('Z', 'Y')
    mat = bpy.data.materials.new('hm'); mat.diffuse_color = (0.75, 0.45, 0.2, 1); hm_.materials.append(mat)
    scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
    out = os.environ['GRIP_RENDER']+'_final'
    # cameras in the hand's own frame: down the handle, from the palm side, from the back, from the finger side
    for vname, d in (('axis', A), ('palm', nrm), ('back', -nrm), ('side', np.cross(A, nrm)), ('tips', -fdir)):
        d = Vector(d).normalized(); up = Vector(fdir) if abs(Vector(fdir) @ d) < 0.9 else Vector(A)
        cam = common.ortho_camera('c_' + vname, Vector(C) + d * 1.0, (0, 0, 0), float(os.environ.get('GRIP_SCALE', '0.24')))
        cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
        scene.camera = cam; scene.render.resolution_x = scene.render.resolution_y = 360
        scene.render.filepath = f'{out}_{vname}.png'; bpy.ops.render.render(write_still=True)
