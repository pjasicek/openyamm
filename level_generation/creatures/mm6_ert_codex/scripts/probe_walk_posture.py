import bpy,json,math,sys
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];out=P/'review/walk_posture_v2'
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_ert.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['EarthElemental'];scene=bpy.context.scene
report={};poses={}
for clip,t in [('Standing',0),('Walking',0),('Walking',.35),('Walking',.70),('Walking',1.05)]:
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*60;scene.frame_set(math.floor(f),subframe=f%1);key=f'{clip}_{t}'
 poses[key]={b.name:b.matrix_basis.copy() for b in rig.pose.bones};row={}
 for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle','B_L_UpperArm','B_R_UpperArm']:
  b=rig.pose.bones[n];delta=b.matrix.to_3x3()@b.bone.matrix_local.to_3x3().inverted();row[n]={'local_euler_deg':[round(math.degrees(x),1) for x in b.rotation_quaternion.to_euler()],'world_delta_deg':[round(math.degrees(x),1) for x in delta.to_euler()],'head':list(b.head)}
 report[key]=row
rig.animation_data.action=None
common.workbench_clay(scene);scene.display.shading.color_type='OBJECT';body.color=(.6,.6,.6,1)
for tag,key,zero in [('idle','Standing_0',[]),('before','Walking_0',[]),('clavicles','Walking_0',['B_L_Clavicle','B_R_Clavicle']),('spine','Walking_0',['B_Spine','B_Spine1','B_Spine2']),('both','Walking_0',['B_L_Clavicle','B_R_Clavicle','B_Spine','B_Spine1','B_Spine2'])]:
 for b in rig.pose.bones:b.matrix_basis=poses[key][b.name]
 for n in zero:rig.pose.bones[n].matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();common.render_views(str(out/tag),1.4,2.7,views=('front','left'),resolution=(450,600))
(out/'posture_probe.json').write_text(json.dumps(report,indent=2));print('POSTURE',json.dumps(report))
