"""Clip timing for the engine's action events (playbook "Clip timing"): work/rig_v6.blend -> work/rig_v6t.blend.
- Attack spine twist limit: the source slash turns the chest up to ~90 deg about the spine against the pelvis (110 deg
  shoulder line vs hip line with the clavicles) in the follow-through, about twice a real trunk's axial rotation; the
  neck turns back ~50 deg to keep the head forward. Per frame, the summed twist of B_Spine..B_Spine2 about their
  segment axes is softly limited to TWIST_MAX (unchanged below TWIST_FREE, each bone keeps its share and its swing);
  the removed turn goes to the neck so the head keeps its world direction.
- Attack: a ready pause of LEAD seconds (ease from the Standing pose into the attack's first pose, with a slight
  coil: the chest turned 6 deg toward the sword side) before the source attack at its own
  speed. The blow (peak sword-tip speed of the built clip) then lands near 0.6 s, so the engine's fit of [0, impact]
  to the native 0.75 s action stretches it only ~1.2x. Prints IMPACT for actors.yml `events: attack_melee`.
- Fidget: kept as built (the set's Armed boost 1, 1.0 s at source speed): since 2026-10-10 the engine plays a longer
  fidget to its end while the actor stands. (An interim 0.6 s head shake replaced it while fidgets were cut at the
  native 0.625 s.)
"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
LEAD = 0.4
TWIST_FREE, TWIST_MAX = math.radians(25), math.radians(45)
SPINE = ('B_Spine', 'B_Spine1', 'B_Spine2')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v5.blend'))
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


# Upright native stance: keep the source's breathing and arm motion, with flat bind-pose feet and quiet trunk.
st=bpy.data.actions['Standing']; frames=[]
legs=[f'B_{side}_{name}' for side in 'RL' for name in ('Thigh','Calf','Foot','Toe0')]
for f in range(int(st.frame_range[1])+1):
 pose=sample(st,f)
 for n in ['B_Pelvis',*legs]:pose[n]=(Quaternion(),Vector((0,0,0)))
 for n in (*SPINE,'B_Neck','B_Head'):
  pose[n]=(Quaternion().slerp(pose[n][0],.15),pose[n][1])
 set_act(None)
 for n,(q,l) in pose.items():
  rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
 for side in 'RL':
  arm=rig.pose.bones[f'B_{side}_UpperArm'];el=rig.pose.bones[f'B_{side}_Forearm']
  h=arm.head.copy();direction=el.head-h
  q=direction.rotation_difference(Vector((.07 if side=='L' else -.07,-.015,-1)))
  arm.matrix=Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h)@arm.matrix
  bpy.context.view_layer.update()
  if side=='L':el.rotation_quaternion=Quaternion().slerp(el.rotation_quaternion,.5)
  bpy.context.view_layer.update()
 pose={n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
 frames.append(pose)
write('Standing',frames)
standing=[{n:(q.copy(),l.copy()) for n,(q,l) in row.items()} for row in frames]
# Native fidget: subtle weight shift and glance, with the mace held steadily at the waist.
frames=[]
for f in range(46):
 pose={n:(q.copy(),l.copy()) for n,(q,l) in standing[int(f*60/45)%61].items()}
 t=f/45; a=math.sin(2*math.pi*t)*math.sin(math.pi*t)**2
 pose['B_Spine2']=(pose['B_Spine2'][0]@Quaternion((0,0,1),math.radians(2.5)*a),pose['B_Spine2'][1])
 pose['B_Neck']=(pose['B_Neck'][0]@Quaternion(TWIST_AXES['B_Neck'],math.radians(9)*a),pose['B_Neck'][1])
 frames.append(pose)
write('Fidget',frames)
# ---------------------------------------------------------------- attack with a ready pause
atk = bpy.data.actions['Attack']; st = bpy.data.actions['Standing']
n_atk = int(atk.frame_range[1]); n_lead = int(round(LEAD * FPS))
s0, a0 = sample(st, 0), limit_spine_twist(sample(atk, 0))[0]
frames = []
for i in range(n_lead):
    u = smooth(i / n_lead); coil = math.sin(math.pi * u) * 0.8 + u * 0.2            # coil peaks then holds a little
    pose = {}
    for n in names:
        q = s0[n][0].slerp(a0[n][0], u); l = s0[n][1].lerp(a0[n][1], u)
        if n == 'B_Spine2':
            q = q @ Quaternion((0, 1, 0), math.radians(-6) * coil)
        pose[n] = (q, l)
    frames.append(pose)
worst = (0.0, 0.0)
for f in range(n_atk + 1):
    pose, total, limited = limit_spine_twist(sample(atk, f))
    frames.append(pose)
    if abs(total) > abs(worst[0]):
        worst = (total, limited)
print(f'ATTACK spine twist peak {math.degrees(worst[0]):.0f} deg -> {math.degrees(worst[1]):.0f} deg')
new_atk = write('Attack', frames)
# blow = peak tip speed of the Sword bone tip in the new clip
set_act(new_atk)
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
tips = []
for f in range(len(frames)):
    scene.frame_set(f)
    M = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix          # the Sword bone is added at export
    c = M @ Vector(G['handle_centre_hand_local']); ax = (M.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
    tips.append(np.array(c + ax * 0.40))
sp = np.linalg.norm(np.diff(np.array(tips), axis=0), axis=1)
k = int(np.argmax(sp)); impact = (k + 0.5) / FPS
set_act(None)
print(f'ATTACK {len(frames) / FPS:.3f} s (lead {n_lead / FPS:.3f} s), blow at {impact:.3f} s -> wind-up stretch '
      f'{0.75 / impact:.2f}x; IMPACT {impact:.3f}')

# Ease recovery from the source guard into the upright native idle.
st0=sample(bpy.data.actions['Standing'],0)
for name in ('Attack','Hit'):
 act=bpy.data.actions[name];end=int(act.frame_range[1]); rows=[sample(act,f) for f in range(end+1)]
 for f in range(max(0,end-4),end+1):
  u=smooth((f-(end-4))/4)
  rows[f]={n:(rows[f][n][0].slerp(st0[n][0],u),rows[f][n][1].lerp(st0[n][1],u)) for n in names}
 if name=='Hit':
  for f in range(6):
   u=smooth(f/6);rows[f]={n:(st0[n][0].slerp(rows[f][n][0],u),st0[n][1].lerp(rows[f][n][1],u)) for n in names}
 write(name,rows)
# Left hand relaxes; the right opens as the native death releases the mace.
for name in ('Standing','Fidget','Walking','Running','Attack','Hit','Death'):
 act=bpy.data.actions[name];end=int(act.frame_range[1]); rows=[]
 for f in range(end+1):
  pose=sample(act,f)
  for n in names:
   if n.startswith('B_L_Finger'):
    pose[n]=(Quaternion().slerp(pose[n][0],.55),pose[n][1])
   if name=='Death' and n.startswith('B_R_Finger'):
    pose[n]=(pose[n][0].slerp(Quaternion(),smooth((f-6)/7)),pose[n][1])
  if name=='Death' and f<5:
   u=smooth(f/5);pose={n:(st0[n][0].slerp(pose[n][0],u),st0[n][1].lerp(pose[n][1],u)) for n in names}
  rows.append(pose)
 write(name,rows)
# The left walking hand needs 2 cm clearance from the belt-hung scabbard on this body's proportions.
act=bpy.data.actions['Walking'];rows=[]
for f in range(int(act.frame_range[1])+1):
 pose=sample(act,f);set_act(None)
 for n,(q,l) in pose.items():
  rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
 arm=rig.pose.bones['B_L_UpperArm'];h=arm.head.copy()
 forward=(rig.pose.bones['B_Spine2'].matrix.to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))).normalized()
 arm.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(6),4,forward)@Matrix.Translation(-h)@arm.matrix
 bpy.context.view_layer.update()
 rows.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names})
write('Walking',rows)
# Foot/corpse placement is measured from the deformed mesh, not guessed from the pelvis joint.
body=bpy.data.objects['Body']; ground={}
for name in ('Standing','Fidget','Walking','Running','Attack','Hit','Death'):
 act=bpy.data.actions[name];end=int(act.frame_range[1]);rows=[]; lows=[]
 for f in range(end+1):
  pose=sample(act,f);set_act(None)
  for n,(q,l) in pose.items():
   pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l
  bpy.context.view_layer.update()
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  low=min((body.matrix_world@v.co).z for v in m.vertices);ev.to_mesh_clear();lows.append(low)
  correction=-low if name in ('Standing','Fidget','Walking') else max(0,-low)
  if name=='Death' and low>.16:correction=.16-low
  pel=rig.pose.bones['B_Pelvis'];M=pel.matrix.copy();M.translation.z+=correction;pel.matrix=M
  bpy.context.view_layer.update();pose['B_Pelvis']=(pel.rotation_quaternion.copy(),pel.location.copy());rows.append(pose)
 write(name,rows);ground[name]=[round(min(lows),4),round(max(lows),4)]
print('GROUND initial min/max z',ground)
assert int(bpy.data.actions['Hit'].frame_range[1])/FPS <= .75
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
    CAP = np.radians([30, 0, 0, 15]); COST = np.array([1.0, 0.7, 2.0, 1.5]); STEP = math.radians(2.5)
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


for nm in ('Attack','Death'):
    head_fix(nm)
json.dump({'attack_impact_s':round(impact,3),'native_action_s':.75,'death_source':'ArmedKnockdown1','mace_release_frame':8,'ground_before_correction':ground},open(os.path.join(HERE,'work','clip_timing.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'work','rig_v6.blend'))
