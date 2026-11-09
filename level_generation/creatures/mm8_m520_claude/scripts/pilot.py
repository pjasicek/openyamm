from pathlib import Path
import sys,runpy,os,bpy,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
os.environ['FRADIUS']='.04'
def run(name,args):
 s=p/f'scripts/{name}.py';sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('finger_weights',[p/'work/rig_v1.blend',p/'work/rig_fingers.blend'])
clips={'Standing':'Standard Idle','Walking':'Orc Walk','Running':'Running (5)','Attack':'_discarded/Throw In','Hit':'Standing React Small From Front','Death':'Mutant Dying','Fidget':'Orc Idle (1)'}
run('retarget_mixamo',[p/'work/rig_fingers.blend',p/'work/pilot_raw.blend']+[f'anim_library/mixamo/{v}.fbx:{k}' for k,v in clips.items()])
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
# Rigid neck discs and their holders follow the chest; the arm band follows the right upper arm.
for v in body.data.vertices:
 piece=body.data.attributes['piece'].data[v.index].value
 bone='B_R_UpperArm' if piece==2 else 'B_Spine2' if 3<=piece<=8 else None
 if bone:
  for ge in list(v.groups):body.vertex_groups[ge.group].remove([v.index])
  body.vertex_groups[bone].add([v.index],1,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_raw.blend'))
common.workbench_clay(bpy.context.scene)
for name in clips:
 act=bpy.data.actions[name];rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 for i in range(5):
  frame=int(act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/4);bpy.context.scene.frame_set(frame)
  common.render_views(str(p/f'review/pilot_{name}_{i}'),1.3,3,views=('front','left'),resolution=(450,650))
