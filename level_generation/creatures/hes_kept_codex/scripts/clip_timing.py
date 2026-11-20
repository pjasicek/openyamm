"""Kept stance transitions, source-speed clips, spine limit and measured sole placement."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
LEAD = 0.15                     # ready pause (2026-10-11 slash: 0.15 s puts its slice at the native 0.75 s wind-up)
TWIST_FREE, TWIST_MAX = math.radians(25), math.radians(45)
SPINE = ('B_Spine', 'B_Spine1', 'B_Spine2')
SRC,OUT=sys.argv[sys.argv.index('--')+1:]
KIND=os.environ['KEPT_BODY']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']
names = [b.name for b in rig.data.bones]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def segment_axis(j, child):
    b, c = rig.data.bones[j], rig.data.bones[child]
    return (b.matrix_local.to_3x3().inverted() @ (c.head_local - b.head_local)).normalized()


TWIST_AXES = {'B_Spine': segment_axis('B_Spine', 'B_Spine1'), 'B_Spine1': segment_axis('B_Spine1', 'B_Spine2'),
              'B_Spine2': segment_axis('B_Spine2', 'B_Neck'), 'B_Neck': segment_axis('B_Neck', 'B_Head')}


def split_twist(q, axis):
    """q = swing @ twist about the bone-local axis; returns (swing, twist angle)."""
    t = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)
    t = (t + math.pi) % (2 * math.pi) - math.pi
    return q @ Quaternion(axis, t).inverted(), t


def limit_spine_twist(pose):
    parts = {j: split_twist(pose[j][0], TWIST_AXES[j]) for j in TWIST_AXES}
    total = sum(parts[j][1] for j in SPINE)
    if abs(total) <= TWIST_FREE:
        return pose, total, total
    span = TWIST_MAX - TWIST_FREE
    limited = math.copysign(TWIST_FREE + span * math.tanh((abs(total) - TWIST_FREE) / span), total)
    k = limited / total
    for j in SPINE:
        swing, t = parts[j]; pose[j] = (swing @ Quaternion(TWIST_AXES[j], t * k), pose[j][1])
    swing, t = parts['B_Neck']; pose['B_Neck'] = (swing @ Quaternion(TWIST_AXES['B_Neck'], t + total - limited),
                                                  pose['B_Neck'][1])
    return pose, total, limited


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act)
    prev = {}
    for i, pose in enumerate(frames):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0:
                q = -q
            prev[n] = q
            pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None)
    return act



body=bpy.data.objects['Body'];vg=[g.name for g in body.vertex_groups]
FEET=np.array([sum(e.weight for e in v.groups if vg[e.group] in ('B_L_Foot','B_R_Foot','B_L_Toe0','B_R_Toe0'))>.5 for v in body.data.vertices])
assert FEET.any()
def apply(p):
    set_act(None)
    for n,(q,l) in p.items():
        pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
    bpy.context.view_layer.update()
def blend(a,b,w):
    return {n:((a[n][0] if a[n][0].dot(b[n][0])>=0 else -a[n][0]).slerp(b[n][0],w),a[n][1].lerp(b[n][1],w)) for n in a}
def lower(p,death=False):
    apply(p);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    z=np.array([(body.matrix_world@v.co).z for v in m.vertices]);ev.to_mesh_clear()
    return float(z.min() if death else z[FEET].min())
ST=sample(bpy.data.actions['Kept_Standing'],0)
# Correct the common transition pose first, so every one-shot has exactly the same endpoint.
z=lower(ST);pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z-=z;pb.matrix=M
bpy.context.view_layer.update();ST['B_Pelvis']=(pb.rotation_quaternion.copy(),pb.location.copy())
if KIND=='male':
    # Falling keeps the selected source's reaching arm; a standing carry folds across the thigh during the fall.
    bpy.data.actions.remove(bpy.data.actions['Kept_ArmedDeath'])
    ad=bpy.data.actions['Kept_Death'].copy();ad.name='Kept_ArmedDeath';ad.use_fake_user=True;set_act(ad)
    grip=json.load(open(os.path.join(HERE,'work/male/handle_R.json')))['finger_local']
    for f in range(int(ad.frame_range[1])+1):
        for n,q in grip.items():
            pb=rig.pose.bones[n];pb.rotation_quaternion=Quaternion(q);pb.keyframe_insert('rotation_quaternion',frame=f)
    set_act(None)
report={}
for name in sorted(a.name for a in bpy.data.actions if a.name.startswith('Kept_')):
    action=bpy.data.actions[name];role=name.removeprefix('Kept_').removeprefix('Armed')
    if KIND=='female' and role=='MaceAttack':bpy.data.actions.remove(action);continue
    poses=[sample(action,f) for f in range(int(action.frame_range[1])+1)]
    home=ST
    if name.startswith('Kept_Armed') or role=='MaceAttack':
        home=sample(bpy.data.actions['Kept_ArmedStanding'],0)
    limits=[]
    for f,p in enumerate(poses):
        p,old,new=limit_spine_twist(p);limits.append((old,new))
        fi={'Attack':.15,'MaceAttack':.15,'Hit':.2,'Death':.25,'Fidget':.15}.get(role,0)*30
        fo={'Attack':.2,'MaceAttack':.2,'Hit':.2,'Fidget':.15}.get(role,0)*30
        w=min(smooth(f/fi) if fi else 1,smooth((len(poses)-1-f)/fo) if fo else 1)
        poses[f]=blend(home,p,w)
    lows=np.array([lower(p,role=='Death') for p in poses]);g=np.exp(-.5*(np.arange(-3,4)/.7)**2);g/=g.sum()
    dz=-np.convolve(np.pad(lows,3,mode='edge'),g,'valid')
    if role=='Running':dz=np.maximum(dz,0)
    for f,p in enumerate(poses):
        apply(p);pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z+=float(dz[f]);pb.matrix=M
        bpy.context.view_layer.update();p['B_Pelvis']=(pb.rotation_quaternion.copy(),pb.location.copy())
    if role in ('Standing','Walking','Running'):poses[-1]=poses[0]
    write(name,poses)
    report[name]={'frames':len(poses),'duration_s':(len(poses)-1)/FPS,'max_spine_twist_before_deg':max(abs(math.degrees(x[0])) for x in limits),'max_spine_twist_after_deg':max(abs(math.degrees(x[1])) for x in limits),'floor_before_m':[float(lows.min()),float(lows.max())]}
    if role=='Death':write(name.replace('Death','Dead'),[poses[-1],poses[-1]])
    print('TIMING',name,report[name],flush=True)
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
Path=__import__('pathlib').Path
(Path(HERE)/'review'/KIND/'clip_timing.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
