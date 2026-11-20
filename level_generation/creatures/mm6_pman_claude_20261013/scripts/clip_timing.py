"""Keep library motion at source speed; ease one-shot endpoints to the chosen civilian Standing pose."""
from pathlib import Path
import bpy,json,math
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/weighted_v1.blend'))
scene=bpy.context.scene;FPS=30;scene.render.fps=FPS;scene.render.fps_base=1
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=[b.name for b in rig.data.bones]
BLEND_IN={'Hit':0.12,'Death':0.25,'Fidget':0.18}
BLEND_OUT={'Hit':0.16,'Fidget':0.18}
def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


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


def blend_ends(name, frames_or_act):
    st_pose = sample(bpy.data.actions['Standing'], 0)
    if isinstance(frames_or_act, list):
        poses = frames_or_act
    else:
        poses = [sample(frames_or_act, f) for f in range(int(frames_or_act.frame_range[1]) + 1)]
    n = len(poses); fi, fo = BLEND_IN.get(name, 0) * FPS, BLEND_OUT.get(name, 0) * FPS
    out = []
    for i, pose in enumerate(poses):
        w = 1.0
        if fi:
            w = min(w, smooth(i / fi))
        if fo:
            w = min(w, smooth((n - 1 - i) / fo))
        out.append({k: (st_pose[k][0].slerp(q, w) if q.dot(st_pose[k][0]) >= 0 else (-st_pose[k][0]).slerp(q, w),
                        st_pose[k][1].lerp(l, w)) for k, (q, l) in pose.items()})
    return out



for name in ('Hit','Death','Fidget'):
 write(name,blend_ends(name,bpy.data.actions[name]))
# Close genuine looping source clips and make quaternion interpolation continuous.
for name in ('Standing','Walking'):
 act=bpy.data.actions[name];poses=[sample(act,f) for f in range(int(act.frame_range[1])+1)]
 poses[-1]=poses[0];write(name,poses)
# Dead is precisely the last death pose, held for one sample interval.
pose=sample(bpy.data.actions['Death'],39);write('Dead',[pose,pose])
report={}
for name in ('Standing','Walking','Hit','Fidget','Death','Dead'):
 act=bpy.data.actions[name];floors=[]
 for f in range(int(act.frame_range[1])+1):
  set_act(act);scene.frame_set(f)
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
  floors.append(min((body.matrix_world@v.co).z for v in mesh.vertices));ev.to_mesh_clear()
 report[name]={'seconds':float(act.frame_range[1])/FPS,'min_z':min(floors),'max_min_z':max(floors),'floor_by_frame':floors}
 print('FLOOR',name,report[name]['min_z'],report[name]['max_min_z'])
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
(P/'work/motion_floor_v1.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/timed_v1.blend'))
