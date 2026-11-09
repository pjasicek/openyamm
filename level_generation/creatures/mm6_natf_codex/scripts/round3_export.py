import bpy,sys,json,numpy as np,runpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3_cloth.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();objects=[bpy.data.objects[n]for n in ['Body','ForearmBlade','LeafShield']];report={}
for role in ['Running','Attack']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];low=1e9;loc=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));lo,hi=common.world_bounds(objects);low=min(low,lo.z);loc.append((float(f),root.location.copy()))
 dz=max(0,.002-low)
 for f,l in loc:root.location=l+inv@Vector((0,0,dz));root.keyframe_insert('location',frame=f)
 report[role]={'constant_floor_offset_m':dz,'lowest_before_m':low}
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/accepted_master.blend'))
(P/'review/round3/floor.json').write_text(json.dumps(report,indent=2))
s=P/'scripts/round2_opening.py';exec(compile(s.read_text().replace('for a in bpy.data.actions:',"for a in [bpy.data.actions[n] for n in ['Running','Attack']]:").replace('review/round2/hem_opening.json','review/round3/hem_opening.json'),str(s),'exec'))
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
