"""All selected levels against the accepted rig; no animation edits and no runtime installation."""
import bpy,os,sys,json,runpy,hashlib,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_reduction';sys.dont_write_bytecode=True
levels=json.loads((R/'selected.json').read_text())['levels'];results=json.loads((R/'gate_summary.json').read_text());baseline_signature=results['baseline']['rig_animation_signature'];levels=[x for x in levels if x['level']==2]

def signature():
    rig=bpy.data.objects['Rig'];bones=[(b.name,list(b.parent.name if b.parent else ''),[list(row)for row in b.matrix_local])for b in rig.data.bones]
    actions=[]
    for a in sorted(bpy.data.actions,key=lambda a:a.name):
        curves=[fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
        actions.append((a.name,[(fc.data_path,fc.array_index,[(list(k.co),k.interpolation)for k in fc.keyframe_points])for fc in curves]))
    return hashlib.sha256(json.dumps((bones,actions)).encode()).hexdigest()

def anatomy():
    rig=bpy.data.objects['Rig'];sc=bpy.context.scene;report={}
    for act in bpy.data.actions:
        rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];values={sd:[]for sd in 'LR'}
        for i in range(round(act.frame_range[1]/30*48)+1):
            frame=i*30/48;sc.frame_set(int(frame),subframe=frame-int(frame))
            for sd in 'LR':
                upper=rig.pose.bones[f'B_{sd}_UpperArm'];elbow=rig.pose.bones[f'B_{sd}_Forearm'];hand=rig.pose.bones[f'B_{sd}_Hand']
                a=(elbow.head-upper.head).normalized();b=(hand.head-elbow.head).normalized();axis=upper.matrix.to_3x3().col[2].normalized()
                flex=-math.degrees(math.atan2(axis.dot(a.cross(b)),a.dot(b)));off=math.degrees(math.asin(max(-1,min(1,axis.dot(b)))))
                roll=math.degrees(elbow.rotation_quaternion.to_swing_twist('Y')[1])
                hb=rig.data.bones[f'B_{sd}_Hand'];w=hb.head_local;k=rig.data.bones[f'B_{sd}_Finger2'].head_local
                across=rig.data.bones[f'B_{sd}_Finger1'].head_local-rig.data.bones[f'B_{sd}_Finger4'].head_local
                normal=(k-w).cross(across).normalized()
                if normal.x*w.x>0:normal=-normal
                normal=hand.matrix.to_3x3()@hb.matrix_local.to_3x3().inverted()@normal
                toward=(rig.pose.bones[f'B_{sd}_Thigh'].head-hand.head).normalized()
                palm=math.degrees(math.acos(max(-1,min(1,normal.normalized().dot(toward)))))
                values[sd].append((flex,off,roll,palm))
        report[act.name]={sd:{'elbow_flexion_deg':[min(x[0]for x in v),max(x[0]for x in v)],'max_hyperextension_deg':max(0,-min(x[0]for x in v)),'plane_error_deg':max(abs(x[1])for x in v),'forearm_roll_max_deg':max(abs(x[2])for x in v),'palm_to_thigh_deg':[min(x[3]for x in v),max(x[3]for x in v)]}for sd,v in values.items()}
    (R/'anatomy.json').write_text(json.dumps({'source':'accepted round 0 animations, retained exactly','sample_hz':48,'clips':report,'elbow_limit_deg':5,'elbow_status':'inherited failure in accepted Attack; user explicitly froze clips','palm_gate':'Accepted palm trajectories unchanged at every sample; no held weapon. Thigh direction applies only to relaxed rest, not spell release.'},indent=2)+'\n')

for entry in levels:
    name=str(entry['level']);bpy.ops.wm.open_mainfile(filepath=str(P/entry['blend']));sig=signature()
    if name=='baseline':baseline_signature=sig;anatomy()
    else:assert sig==baseline_signature,('Rig or clips changed',name)
    os.environ['LCH_GATE_BLEND']=entry['blend'];os.environ['LCH_GATE_REPORT']=f'review/triangle_reduction/lod_{name}_rig.json';os.environ['LCH_SKIP_GATE_EXPORT']='1'
    runpy.run_path(str(P/'scripts/measure_rig.py'),run_name='__main__')
    os.environ['LCH_CONTACT_REPORT']=f'review/triangle_reduction/lod_{name}_contacts.json'
    sys.argv=['g6_contacts.py','--',str(P/entry['blend']),'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
    error=None
    try:runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
    except AssertionError as exc:error=str(exc)
    results[name]={'rig_animation_signature':sig,'contact_error':error};(R/'gate_summary.json').write_text(json.dumps(results,indent=2)+'\n')
    print('ROUND1_GATES',name,error,flush=True)
    if name!='baseline':
        os.environ['LCH_EXPORT_BLEND']=entry['blend'];os.environ['LCH_EXPORT_PATH']=f'work/round1/lod{name}_geometry.glb'
        runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
print('ROUND1_GATE_EXPORT_COMPLETE',flush=True)
