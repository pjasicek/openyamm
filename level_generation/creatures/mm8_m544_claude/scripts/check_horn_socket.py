from pathlib import Path
import json,bpy
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'unicorn_master.blend'))
r=bpy.data.objects['Unicorn_Rig'];s=bpy.context.scene
point=Vector((-.009,-.392,.588))
offset=r.data.bones['HornTip'].matrix_local.inverted()@point
report={'release_offset_in_horn_tip':list(offset),'samples':{}}
for name,t in [('Standing',0),('Fidget',.25),('Attack',1.125),('Cast',1.125)]:
 r.animation_data.action=bpy.data.actions[name];s.frame_set(1+int(t*48),subframe=t*48-int(t*48))
 q=r.pose.bones['HornTip'].matrix@offset
 report['samples'][name]=list(q)
 assert (q.x*q.x+q.y*q.y)**.5*389.06<180 and 0<q.z*389.06<240,(name,list(q))
(P/'work/horn_socket.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
