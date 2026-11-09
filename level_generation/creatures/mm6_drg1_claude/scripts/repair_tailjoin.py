"""Keep belly/tail skin on the trunk, blending smoothly into the enlarged hind thighs."""
import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/checkpoint_v4/export/mm6_drg1.blend'))
o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
def ss(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def assign(v,w):
 w={n:x for n,x in sorted(w.items(),key=lambda kv:-kv[1])[:4] if x>1e-6};total=sum(w.values());assert total>0
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 for n,x in w.items():o.vertex_groups[n].add([v.index],x/total,'REPLACE')
changed=[]
for v in o.data.vertices:
 x,y,z=v.co;w={o.vertex_groups[g.group].name:g.weight for g in v.groups}
 if not (-.065<y<.38 and z>.17 and abs(x)<.12 and any('Hind' in n for n in w)):continue
 # Hind legs lie beside/below the tail; proximity to their bones alone mislabels the central belly.
 lateral=ss((abs(x)-.025)/.055);below=1-ss((z-.17)/.045)
 gate=max(lateral,below)*(1-ss((z-.29)/.075))
 removed=sum(a*(1-gate) for n,a in w.items() if 'Hind' in n)
 if removed<1e-6:continue
 w={n:(a*gate if 'Hind' in n else a) for n,a in w.items()}
 tail=ss((y+.025)/.105);second=ss((y-.17)/.14)
 for n,a in [('Spine1',1-tail),('Tail1',tail*(1-second)),('Tail2',tail*second)]:w[n]=w.get(n,0)+removed*a
 assign(v,w);changed.append(v.index)
# Reapply the accepted limb enlargement to these corrected weights from the same v4 rest geometry.
for v in o.data.vertices:
 p=v.co.copy();limbs={o.vertex_groups[g.group].name:g.weight for g in v.groups if 'Fore' in o.vertex_groups[g.group].name or 'Hind' in o.vertex_groups[g.group].name};total=sum(limbs.values())
 if total<.25:continue
 blend=ss((total-.25)/.65);delta=Vector()
 for n,weight in limbs.items():
  b=rig.data.bones[n];axis=(b.tail_local-b.head_local).normalized();d=p-b.head_local;along=axis*d.dot(axis);radial=d-along
  delta+=(radial*.70+along*.35 if n.endswith('Foot') else radial*(.55 if n.endswith('Upper') else .65))*(weight/total)*blend
 v.co+=delta
assert len(changed)>50,changed
assert all(sum(g.weight for g in v.groups)>.999 for v in o.data.vertices)
o.data.update();(P/'review/tailjoin_v6').mkdir(exist_ok=True)
(P/'review/tailjoin_v6/weight_repair.json').write_text(json.dumps({'changed_weight_vertices':len(changed),'indices':changed,'reason':'Central belly/tail incorrectly bound to hind legs; restore trunk/tail ownership before accepted enlargement.'},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/tailjoin_v6_source.blend'))
print('REPAIRED',len(changed))
