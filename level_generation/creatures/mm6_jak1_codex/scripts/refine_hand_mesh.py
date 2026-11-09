import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));ob=bpy.data.objects['Body'];changed=[]
for v in ob.data.vertices:
 x,y,z=v.co
 if .525<abs(x)<.585 and .939<z<.996 and y<-.038:
  v.co.y=-.038;changed.append(v.index)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
(P/'work/hand_web_correction.json').write_text(json.dumps({'vertices':changed,'reason':'Flatten capped duplicated-branch roots into the palm surface; keep surviving digits.'},indent=2))
