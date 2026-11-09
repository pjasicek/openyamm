from pathlib import Path
import bpy,json,sys,math
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
out=P/'review/arm_20261016';out.mkdir(exist_ok=True)
reports={}
for stage in ('rig_refined_grip','rig_carry','rig_textured_uv'):
 bpy.ops.wm.open_mainfile(filepath=str(P/'work'/f'{stage}.blend'))
 rig=bpy.data.objects['Rig'];sc=bpy.context.scene; report={}
 for clip in ('Standing','Walking','Running','Hit','Death','Fidget'):
  act=bpy.data.actions.get(clip)
  if not act:continue
  rig.animation_data.action=act
  if len(act.slots):rig.animation_data.action_slot=act.slots[0]
  frames=[]
  for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
   sc.frame_set(f)
   chest=rig.pose.bones['B_Spine2'].matrix.inverted();r={}
   for sd in 'LR':
    names=[f'B_{sd}_{n}' for n in ('UpperArm','Forearm','Hand')]
    S,E,W=[rig.pose.bones[n].head.copy() for n in names]
    u=(E-S).normalized();v=(W-E).normalized();local=chest.to_3x3()@u
    r[sd]={'joints':[list(p) for p in (S,E,W)],'bend':math.degrees(u.angle(v)),
      'lateral_abduction':math.degrees(math.asin(max(-1,min(1,local.x*(1 if sd=='L' else -1))))),
      'elbow_below_shoulder':S.z-E.z}
   frames.append({'frame':f,**r})
  report[clip]=frames
  if clip=='Running':
   print(stage,clip,[(sd,round(max(r[sd]['lateral_abduction'] for r in frames),1),round(max(r[sd]['bend'] for r in frames),1)) for sd in 'LR'])
  if clip=='Running' and stage in ('rig_refined_grip','rig_textured_uv'):
   for frame in (0,5,11,16):
    sc.frame_set(frame);common.workbench_clay(sc)
    common.render_views(str(out/f'{stage}_run_{frame}'),1.2,1.2,views=('front','rside60'),resolution=(600,600))
 reports[stage]=report
(out/'probe.json').write_text(json.dumps(reports,indent=2)+'\n')
