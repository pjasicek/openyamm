"""Clone the selected Mutant source frames in world space, keeping the established B_* role names."""
import bpy,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];repo=P.parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(repo/'anim_library/mixamo/Mutant Breathing Idle.fbx'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');W=arm.matrix_world
mapping={'B_Pelvis':'Hips','B_Spine':'Spine','B_Spine1':'Spine1','B_Spine2':'Spine2','B_Neck':'Neck','B_Head':'Head'}
for sd,side in [('L','Left'),('R','Right')]:
    for dst,src in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]:mapping[f'B_{sd}_{dst}']=side+src
    for i,f in enumerate(['Thumb','Index','Middle','Ring','Pinky']):
        for j,suffix in enumerate(['','1','2']):
            dst=f'B_{sd}_Finger{i}'+suffix
            if sd=='R' and i==0 and j:dst=f'B_R_Finger0.00{j}'
            mapping[dst]=f'{side}Hand{f}{j+1}'
reverse={v:k for k,v in mapping.items()};out={}
bpy.context.scene.frame_set(int(arm.animation_data.action.frame_range[0]))
bpy.context.view_layer.update()
for name,source in mapping.items():
    bone=arm.data.bones['mixamorig:'+source];M=W@bone.matrix_local
    children=[c for c in bone.children if c.name.removeprefix('mixamorig:') in reverse]
    prefer={'Hips':'Spine','Spine2':'Neck','LeftHand':'LeftHandMiddle1','RightHand':'RightHandMiddle1'}
    child=next((c for c in children if c.name=='mixamorig:'+prefer.get(source,'')),children[0] if children else None)
    par=bone.parent.name.removeprefix('mixamorig:') if bone.parent else ''
    out[name]={'parent':reverse.get(par),'head':list(M.translation),'rot':[list(r) for r in M.to_3x3().normalized()],
               'standing_delta':[list(r) for r in (W@arm.pose.bones[bone.name].matrix).to_3x3().normalized()@M.to_3x3().normalized().inverted()],
               'child':reverse[child.name.removeprefix('mixamorig:')] if child else None,
               'seg':list((W@child.matrix_local).translation-M.translation) if child else None}
assert len(out)==52 and out['B_Pelvis']['parent'] is None,len(out)
(P/'work/source_rest.json').write_text(json.dumps(out,indent=2)+'\n')
(P/'work/source_bone_map.json').write_text(json.dumps(mapping,indent=2)+'\n')
print('SOURCE',len(out),'bones from Mutant Breathing Idle, world frames preserved',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
