"""Anatomical fields for a single continuous coat; no added shoulder geometry."""
import bpy,sys,json,numpy as np,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
selection=json.loads((P/'review/reduction/selection.json').read_text());report=[]
def smooth(t):t=float(np.clip(t,0,1));return t*t*(3-2*t)
def put(o,v,w):
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 w=dict(sorted(w.items(),key=lambda t:-t[1])[:4]);total=sum(w.values())
 for n,x in w.items():
  if x>1e-8:o.vertex_groups[n].add([v.index],float(x/total),'REPLACE')
for entry in [{'blend':'work/round2/master.blend'}]+selection['body']:
 p=P/entry['blend'];bpy.ops.wm.open_mainfile(filepath=str(p.parent/('before_basic_'+p.name)));C.reset();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];part=np.array([a.value for a in o.data.attributes['piece'].data])
 for v in o.data.vertices:
  sd='L'if v.co.x>0 else'R';x,y,z=v.co
  if part[v.index]==0 and z<1.5:
   h=smooth((z-1.4)/.1);put(o,v,{'B_Neck':1-h,'B_Head':h});continue
  if part[v.index]!=1:continue
  elbow=r.data.bones[f'B_{sd}_Forearm'].head_local;wrist=r.data.bones[f'B_{sd}_Hand'].head_local;axis=(wrist-elbow).normalized()
  old={o.vertex_groups[g.group].name:g.weight for g in v.groups};share=sum(w for n,w in old.items()if n.startswith(f'B_{sd}_') and any(t in n for t in ['Arm','Hand','Clavicle']))
  arm=smooth((share-.08)/.72)
  arm*=max(smooth((abs(x)-.27)/.08),smooth((z-1.04)/.20))
  fore=smooth(((v.co-elbow).dot(axis)+.075)/.15)
  hand=smooth(((v.co-wrist).dot(axis)+.065)/.055)
  w={f'B_{sd}_UpperArm':arm*(1-fore),f'B_{sd}_Forearm':arm*fore*(1-hand),f'B_{sd}_Hand':arm*fore*hand}
  waist=smooth((1.17-z)/.22);neck=smooth((z-1.39)/.085)*smooth((.18-abs(x))/.055)
  w['B_Pelvis']=(1-arm)*waist;w['B_Spine2']=(1-arm)*(1-waist)*(1-neck);w['B_Neck']=(1-arm)*(1-waist)*neck
  put(o,v,w)
 bpy.ops.wm.save_as_mainfile(filepath=str(p));report.append({'blend':entry['blend'],'shirt_vertices':int((part==1).sum()),'method':'Fresh Meshy garment segmentation with smooth anatomical arm chain weights; no distant torso weights beyond elbow. Matching neck/collar field.'})
(P/'review/round2/continuous_shirt_weights.json').write_text(json.dumps(report,indent=2))
