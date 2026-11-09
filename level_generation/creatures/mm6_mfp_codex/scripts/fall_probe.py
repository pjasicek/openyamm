import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;common.workbench_clay(sc)
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
rows=[]
for j,f in enumerate([8,15,24,27,32,77]):
 sc.frame_set(f);lo,hi=common.world_bounds([b]);C=(lo+hi)/2;span=max(1.9,hi.z-lo.z+.2,(hi.y-lo.y)*1.5,(hi.x-lo.x)*1.5)
 common.render_views(str(P/'review/fall_probe'/f'{j:02}'),C.z,span,views=('front','left','three_quarter'),resolution=(300,450),target=(C.x,C.y))
 rows.append({'frame':f,'joints':{pb.name:list(pb.head)for pb in r.pose.bones if any(x in pb.name for x in ['Pelvis','Spine','Neck','Head','Thigh','Calf','Foot','UpperArm','Forearm','Hand'])}})
(P/'review/fall_probe.json').write_text(json.dumps(rows,indent=2))
