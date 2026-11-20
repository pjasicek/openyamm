"""Measure final world-rotation steps against the selected local animation sources."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
import numpy as np
P=Path(__file__).resolve().parents[1]
BONES=['B_Head','B_Neck','B_Spine2','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_UpperArm','B_L_Forearm','B_L_Hand','B_L_Foot','B_R_Foot']
def measure(rig, act, fps):
    rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    start,end=act.frame_range
    ts=np.arange(start,end+1e-6,fps/48)
    qs={n:[] for n in BONES}; bends={s:[] for s in ['L','R']}
    for f in ts:
        bpy.context.scene.frame_set(int(f),subframe=float(f%1))
        for n in BONES:qs[n].append((rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion())
        for side in bends:
            wrist=rig.pose.bones[f'B_{side}_Hand'].head
            fore=wrist-rig.pose.bones[f'B_{side}_Forearm'].head
            palm=sum((rig.pose.bones[f'B_{side}_Finger{i}'].head for i in range(1,5)),Vector())/4-wrist
            bends[side].append(math.degrees(fore.angle(palm)))
    out={}
    for n,q in qs.items():
        steps=np.array([math.degrees(a.rotation_difference(b).angle) for a,b in zip(q[:-1],q[1:])])
        steps=np.minimum(steps,360-steps);d2=np.abs(np.diff(steps))
        out[n]={'step':float(steps.max()),'step_time':float(ts[steps.argmax()]/fps),
                'second_difference':float(d2.max()),'difference_time':float(ts[d2.argmax()]/fps)}
    return {'bones':out,'anatomical_wrist_bend':{s:{'max':max(v),'time':float(ts[np.argmax(v)]/fps)}for s,v in bends.items()}}
bpy.ops.wm.open_mainfile(filepath=str(P/'export/m628_master.blend'))
rig=bpy.data.objects['Rig'];bpy.context.scene.render.fps=30
final={a.name:measure(rig,a,30) for a in bpy.data.actions}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P.parents[2]/'anim_library/humanoid_set/2Hand Bow.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
selected=['2HandBowIdle','2HandBowWalk','2HandBowAttack1','2HandBowGetHitF1','2HandBowDeath1']
source={a.name:measure(rig,a,30) for a in bpy.data.actions if a.name.split('|')[-1].split('@')[-1] in selected}
assert len(final)==7 and len(source)==5
(P/'work/final_motion_audit.json').write_text(json.dumps({'sample_rate':48,'final':final,'source':source},indent=2)+'\n')
for n,r in final.items():
    print(n,'wrist',r['anatomical_wrist_bend'],'largest step',max((v['step'],b)for b,v in r['bones'].items()))
