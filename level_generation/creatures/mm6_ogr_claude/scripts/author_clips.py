"""Native Ogre stance, guard fidget and forward collapse; source R6 slash with a ready lead."""
from pathlib import Path
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
SRC_BLEND = str(Path(__file__).resolve().parents[1]/'work/rig_v5.blend')
OUT_BLEND = str(Path(__file__).resolve().parents[1]/'work/rig_v5t.blend')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
LEAD = 0.4                           # SwordAttackR6 blow at 0.28 s -> ~0.68 s (R4, a lunging stab, was replaced)
CAST_LEAD = 0.4                      # ArmedCastLAttack1 thrust at 0.25 s -> ~0.65 s
FIDGET_LEN = 0.75                    # native gobfi: six 125 ms frames
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC_BLEND))
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


SPINE = ('B_Spine','B_Spine1','B_Spine2')
TWIST_FREE=math.radians(30)
TWIST_MAX=math.radians(45)
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



body=bpy.data.objects['Body']; W=rig.matrix_world

def apply(pose):
 set_act(None)
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update()

def current():
 return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}

def turn(n,axis,deg):
 pb=rig.pose.bones[n]; m=W@pb.matrix; h=m.translation.copy()
 pb.matrix=W.inverted()@(Matrix.Translation(h)@Matrix.Rotation(math.radians(deg),4,Vector(axis))@Matrix.Translation(-h)@m)
 bpy.context.view_layer.update()

def aim(n,child,direction):
 pb=rig.pose.bones[n];m=pb.matrix.copy()
 d=rig.pose.bones[child].head-pb.head
 q=d.rotation_difference(Vector(direction))
 R=q.to_matrix()@m.to_3x3();M=R.to_4x4();M.translation=m.translation;pb.matrix=M
 bpy.context.view_layer.update()

def floor_pose():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
 low=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
 root=rig.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z-=low;root.matrix=m
 bpy.context.view_layer.update()

# Native upright stance: fixed planted legs, restrained breathing and a forward/upward sword.
old=bpy.data.actions['Standing'];frames=[]
walk0=sample(bpy.data.actions['Walking'],0)
for i in range(61):
 pose={n:(q.copy(),l.copy()) for n,(q,l) in walk0.items()}
 for n in names:
  if any(n==f'B_{s}_{b}' for s in 'LR' for b in ('Thigh','Calf','Foot','Toe0')) or n=='B_Pelvis':
   pose[n]=(Quaternion(),Vector())
  elif n in ('B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'):
   pose[n]=walk0[n]
 apply(pose)
 turn('B_Spine2',(1,0,0),math.sin(i/60*2*math.pi)*0.7)
 turn('B_R_Forearm',(1,0,0),-30)
 floor_pose();frames.append(current())
write('Standing',frames)
standing=frames[0]

# Preserve the source slash at its intended speed after a 0.4-second ready lead.
atk=bpy.data.actions['Attack'];source=[limit_spine_twist(sample(atk,i))[0] for i in range(int(atk.frame_range[1])+1)]
frames=[]
for i in range(12):
 u=smooth(i/12);frames.append({n:(standing[n][0].slerp(source[0][n][0],u),standing[n][1].lerp(source[0][n][1],u)) for n in names})
frames+=source
write('Attack',frames)
# Fidget: native sword lifts diagonally across chest while the free hand guards the belly.
frames=[]
for i in range(23):
 bump=math.sin(math.pi*i/22)**2
 apply(standing)
 turn('B_R_UpperArm',(0,0,1),35*bump)
 turn('B_L_UpperArm',(0,0,1),-25*bump)
 turn('B_R_Forearm',(1,0,0),-35*bump)
 turn('B_L_Forearm',(1,0,0),-60*bump)
 frames.append(current())
write('Fidget',frames)

# Native forward collapse: recoil, knees fold, chest falls, face-down remains with held sword across the front.
keys=[]
apply(standing);keys.append((0,current()))
apply(standing);turn('B_Spine2',(1,0,0),-12);turn('B_L_UpperArm',(0,-1,0),20);keys.append((5,current()))
for frame,bend,rootpitch in [(13,100,20),(20,125,55),(28,20,90)]:
 apply(standing)
 turn('B_Pelvis',(1,0,0),rootpitch)
 for side in 'LR':
  turn(f'B_{side}_Thigh',(1,0,0),-bend*0.5)
  turn(f'B_{side}_Calf',(1,0,0),bend)
 turn('B_Spine2',(1,0,0),12 if frame<28 else 0)
 if frame==28:
  # Arms reach the ground ahead of the chest; sword lies across the collapsed body.
  aim('B_R_UpperArm','B_R_Forearm',(-0.25,-0.05,-0.10))
  aim('B_R_Forearm','B_R_Hand',(0.05,-0.26,-0.03))
  aim('B_L_UpperArm','B_L_Forearm',(0.25,-0.05,-0.10))
  aim('B_L_Forearm','B_L_Hand',(-0.05,-0.26,-0.03))
  g=json.load(open(os.path.join(HERE,'work/grip_pose.json')))
  pb=rig.pose.bones['B_R_Hand'];m=pb.matrix.copy()
  axis=m.to_3x3()@Vector(g['handle_axis_hand_local'])
  R=axis.rotation_difference(Vector((1,-0.25,0.05))).to_matrix()@m.to_3x3()
  M=R.to_4x4();M.translation=m.translation;pb.matrix=M;bpy.context.view_layer.update()
 turn('B_L_UpperArm',(0,-1,0),15 if frame<28 else 0)
 floor_pose();keys.append((frame,current()))
keys.append((36,keys[-1][1]))
frames=[]
for i in range(37):
 j=next((k for k in range(len(keys)-1) if keys[k][0]<=i<=keys[k+1][0]),len(keys)-2)
 a,pa=keys[j];b,pb=keys[j+1];u=smooth((i-a)/(b-a))
 apply({n:(pa[n][0].slerp(pb[n][0],u),pa[n][1].lerp(pb[n][1],u)) for n in names})
 floor_pose();frames.append(current())
write('Death',frames);write('Dead',[frames[-1],frames[-1]])

# ---------------------------------------------------------------- head clear of the shoulders
# gob2 review 2: in the attack's follow-through (0.70-1.0 s, after the blow) the source shrugs the right clavicle and
# the raised shoulder plate sank >= 5 cm into the jaw (the source mannequin has a long neck and no pauldrons); the
# cast's raised left arm and the fall did the same. Per frame one parameter t in 0..1 lifts the chin (neck + head
# extension, t x 35 deg), lowers the offending clavicle and swings that upper arm down (t x 25 deg each); the smallest t that leaves no head vertex more than 3 mm inside the shoulder geometry is found by
# bisection, then held over +-2 frames and smoothed. A sideways neck turn alone needed > 40 deg.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g6_head_clearance import Clearance
DEPTH = 0.003
CL = Clearance(bpy.data.objects['Body'])
W_ = rig.matrix_world
_b = bpy.data.objects['Body']; _hv = [v.co for v in _b.data.vertices if v.co.z > rig.data.bones['B_Head'].head_local.z and v.co.y < -0.08]
FACE_C = sum(_hv, Vector()) / max(len(_hv), 1)                     # rest face centre (front of the head)


def turn_world(n, axis, ang):
    pb = rig.pose.bones[n]; m = W_ @ pb.matrix; h = m.translation.copy()
    pb.matrix = W_.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-h) @ m)
    bpy.context.view_layer.update()


def head_fix(name):
    act = bpy.data.actions[name]; n_f = int(act.frame_range[1]); poses = [sample(act, f) for f in range(n_f + 1)]
    set_act(None)

    def apply(pose):
        for n in names:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = pose[n]
        bpy.context.view_layer.update()

    def correct(side, c):
        # c = (chin up, clavicle down, upper arm down, head away) in radians. The chest twists and the raised upper arm
        # swings under the chin while the head pitches down onto it (it hits the deltoid more than the plate).
        # Directions verified one by one on the worst frames (a probe per component).
        P = lambda n: W_ @ rig.pose.bones[n].head
        lat = (P('B_L_UpperArm') - P('B_R_UpperArm')).normalized()
        cl, sh = P(f'B_{side}_Clavicle'), P(f'B_{side}_UpperArm')
        turn_world(f'B_{side}_Clavicle', (sh - cl).cross(Vector((0, 0, 1))).normalized(), -c[1])   # + lifts
        el, sh = P(f'B_{side}_Forearm'), P(f'B_{side}_UpperArm')
        arm_ax = (el - sh).cross(Vector((0, 0, 1)))
        if arm_ax.length > 1e-4:
            turn_world(f'B_{side}_UpperArm', arm_ax.normalized(), -c[2])                             # + lifts
        turn_world('B_Neck', lat, c[0] * 0.5); turn_world('B_Head', lat, c[0] * 0.5)                  # + chin up
        nk, hd, sh = P('B_Neck'), P('B_Head'), P(f'B_{side}_UpperArm')
        u = (hd - nk).normalized(); v = hd - sh; v = (v - u * v.dot(u)).normalized()
        turn_world('B_Neck', u.cross(v).normalized(), c[3])                                           # away

    # caps and visual costs: lowering the shoulder and arm in a follow-through reads better than a head looking up and
    # away (first version: chin up 30 + away 20 deg made the head look sideways at the sky); the arm stays a last resort
    # disabled (35 deg drove the forearm 5 cm and the blade 18 cm into the body, 15 deg still put the blade 2.8 cm into
    # the left thigh in the low sweep: g6_contacts / g6_sword_mesh)
    CAP = np.radians([25, 25, 0, 12]); COST = np.array([1.0, 0.7, 2.0, 1.5]); STEP = math.radians(2.5)
    cs, sides = [], []
    for pose in poses:
        apply(pose); r = CL.measure()
        c = np.zeros(4)
        if r[0] > DEPTH:
            depth = r[0]
            for _ in range(40):
                best = None
                for k in range(4):
                    if c[k] + STEP > CAP[k] + 1e-6:
                        continue
                    c2 = c.copy(); c2[k] += STEP
                    apply(pose); correct(r[2], c2); d2 = CL.measure()[0]
                    gain = (depth - d2) / COST[k]
                    if best is None or gain > best[2]:
                        best = (d2, k, gain)
                if best is None:
                    break
                c[best[1]] += STEP; depth = best[0]
                if depth <= DEPTH:
                    break
        cs.append(c); sides.append(r[2] if c.any() else None)
    C = np.array(cs); held = np.array([C[max(0, i - 2):i + 3].max(0) for i in range(len(C))])
    k = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); k /= k.sum()
    sm = np.maximum(np.stack([np.convolve(np.pad(held[:, j], 4, mode='edge'), k, mode='valid') for j in range(4)], 1), C)
    out, left = [], []
    for i, pose in enumerate(poses):
        apply(pose)
        if sm[i].any():
            sd = next((sides[j] for j in sorted(range(len(sides)), key=lambda j: abs(j - i)) if sides[j]), 'R')
            correct(sd, sm[i])
        left.append(CL.measure()[0])
        out.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names})
    write(name, out)
    mx = np.degrees(sm.max(0)).round().astype(int)
    print(f'HEADFIX {name}: frames corrected {int(sm.any(1).sum())} of {len(sm)}; max chin up {mx[0]}, clavicle down '
          f'{mx[1]}, arm down {mx[2]}, head away {mx[3]} deg; worst remaining depth {max(left) * 100:.1f} cm')


for nm in ('Attack', 'Hit', 'Running', 'Death', 'Attack'):
    head_fix(nm)

write('Dead',[sample(bpy.data.actions['Death'],36)]*31)

# Re-bake the existing twist bones after authored changes, without modifying their weights again.
FA=0.5;UA=0.5
code=(Path(__file__).parent/'twist_bones.py').read_text()
code=code[code.index('def twist_about'):code.index('bpy.ops.wm.save_as_mainfile')]
exec(compile(code,'twist_bake','exec'))
# Impact from the blade axis, with native gameplay timing unchanged.
g=json.load(open(os.path.join(HERE,'work/grip_pose.json')));pts=[]
act=bpy.data.actions['Attack'];set_act(act)
for i in range(int(act.frame_range[1])+1):
 scene.frame_set(i);m=W@rig.pose.bones['B_R_Hand'].matrix
 pts.append(np.array(m@(Vector(g['handle_centre_hand_local'])+Vector(g['handle_axis_hand_local'])*0.80)))
impact=(int(np.argmax(np.linalg.norm(np.diff(pts,axis=0),axis=1)))+0.5)/FPS
assert 0.60<=impact<=0.9
json.dump({'attack_impact_s':round(impact,3),'native_attack_s':0.75},open(os.path.join(HERE,'work/clip_timing.json'),'w'),indent=2)
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print('AUTHORED',{'impact':impact,'clips':{a.name:list(a.frame_range) for a in bpy.data.actions if a.use_fake_user}})
