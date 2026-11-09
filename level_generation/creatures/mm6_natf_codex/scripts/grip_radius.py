import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/gate_master.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['LeafShield'];M=rig.data.bones['LeafShield'].matrix_local;iv=M.inverted();count=0
for v in ob.data.vertices:
 p=iv@v.co;r=math.hypot(p.y-.045,p.z-.26)
 if abs(p.x)<.0751 and abs(r-.012)<.0001:p.y=.045+(p.y-.045)*11/12;p.z=.26+(p.z-.26)*11/12;v.co=M@p;count+=1
assert count==32,count
(P/'review/grip_radius.json').write_text(json.dumps({'radius_m':.011,'vertices':count,'purpose':'Palm gap 1.8 mm; eliminate the former 1 mm index-finger intersection'},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/accepted_master.blend'))
