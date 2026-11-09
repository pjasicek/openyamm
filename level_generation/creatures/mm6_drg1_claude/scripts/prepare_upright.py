"""Correct box-selected tail/hip and shoulder weights exposed by upright posing; preserve mesh and UVs."""
import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/checkpoint_v2/export/mm6_drg1.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];counts={'hip_tail':0,'shoulders':0}
def distance(p,n):
 b=rig.data.bones[n];h=np.array(b.head_local);d=np.array(b.tail_local)-h;u=np.clip(np.dot(p-h,d)/np.dot(d,d),0,1);return np.linalg.norm(p-h-u*d)
def assign(v,w):
 w={n:x for n,x in sorted(w.items(),key=lambda kv:-kv[1])[:4] if x>1e-5};total=sum(w.values());assert total>0
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 for n,x in w.items():o.vertex_groups[n].add([v.index],float(x/total),'REPLACE')
for v in o.data.vertices:
 x,y,z=v.co;side='L' if x>0 else 'R';old={o.vertex_groups[g.group].name:g.weight for g in v.groups}
 if .025<y<.35 and z<.32 and any('Hind' in n or n.startswith('Tail') or n=='Spine1' for n in old):
  names=[side+'Hind'+part for part in ['Upper','Lower','Foot']]+['Spine1','Tail1','Tail2','Tail3']
  ds=np.array([distance(np.array(v.co),n) for n in names]);weights=np.exp(-(ds**2-ds.min()**2)/.023**2);assign(v,dict(zip(names,weights)));counts['hip_tail']+=1
 if abs(x)>.06 and -.26<y<.05 and .32<z<.525 and any(n.startswith('Neck') or 'Wing' in n or n.startswith('Spine') for n in old):
  # The original box boundary incorrectly assigned shoulder skin to the bending neck.
  blend=float(np.clip((abs(x)-.075)/.20,0,1));blend=blend*blend*(3-2*blend)
  assign(v,{'Spine2':1-blend,side+'Wing0':blend});counts['shoulders']+=1
assert counts['hip_tail']>100 and counts['shoulders']>50,counts
assert max(len(v.groups) for v in o.data.vertices)<=4
(P/'review/upright').mkdir(exist_ok=True);(P/'review/upright/weight_repair.json').write_text(json.dumps(counts,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/upright_source.blend'));print(counts)
