import json,sys,hashlib,copy,shutil
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];root=p.parents[2];sys.path.insert(0,str(root/'tools'));import normal_map_convention as normal
report={}
for prefix in ['mep','mep_head','mep_staff']:
 a=np.array(Image.open(p/f'textures/{prefix}_normal_1k.png').convert('RGB'));value=normal.measure(a);flip=value<=-.17
 if flip:a[:,:,1]=255-a[:,:,1]
 Image.fromarray(a).save(p/f'work/{prefix}_normal_gl.png');report[prefix]={'original_correlation':value,'flipped':flip,'gl_correlation':normal.measure(a)}
(p/'review/normal_convention.json').write_text(json.dumps(report,indent=2))
s=p/'scripts/export_runtime.py';t=s.read_text().replace('import bpy,json,math,numpy as np','import bpy,json,math,numpy as np,sys')
t=t.replace("p=Path(__file__).resolve().parents[1];sel=", "p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import rebake_final;sel=")
t=t.replace("if 'MergedUV' not in me.uv_layers:me.uv_layers.active.name='MergedUV'", "if 'MergedUV' not in me.uv_layers:me.uv_layers.active.name='MergedUV'\n rebake_final.bake(b,'Body',level);rebake_final.bake(staff,'StaffMesh',level)")
start=t.index(' # Export raw shared base maps.');end=t.index(' for a in list(bpy.data.actions):',start);t=t[:start]+t[end:]
t=t.replace(" neutral(r);b.name=b.data.name='Mep';", " neutral(r);bpy.ops.wm.save_as_mainfile(filepath=str(p/f'work/final_lod{level}.blend'));b.name=b.data.name='Mep';")
t=t.replace('a0=np.array(samples,dtype=object);','')
s.write_text(t)
