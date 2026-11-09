"""Broaden drake limbs around their fitted bones; keep the approved head/neck and UV topology."""
import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/checkpoint_v4/export/mm6_drg1.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];counts={'Fore':0,'Hind':0};maxmove=0
before=[v.co.copy() for v in o.data.vertices]
for v in o.data.vertices:
 p=v.co.copy();w={o.vertex_groups[g.group].name:g.weight for g in v.groups};limbs={n:x for n,x in w.items() if 'Fore' in n or 'Hind' in n}
 total=sum(limbs.values())
 if total<.25:continue
 blend=max(0,min(1,(total-.25)/.65));blend=blend*blend*(3-2*blend);delta=Vector()
 for n,weight in limbs.items():
  bone=rig.data.bones[n];axis=(bone.tail_local-bone.head_local).normalized();d=p-bone.head_local;along=axis*d.dot(axis);radial=d-along
  if n.endswith('Foot'):change=radial*.70+along*.35
  else:change=radial*(.55 if n.endswith('Upper') else .65)
  delta+=change*(weight/total)*blend
 v.co+=delta;maxmove=max(maxmove,delta.length);counts['Fore' if any('Fore' in n for n in limbs) else 'Hind']+=1
assert counts['Fore']>100 and counts['Hind']>100,counts
assert all(v.co==before[v.index] for v in o.data.vertices if before[v.index].z>.55),'Head/neck moved'
assert maxmove<.08,maxmove
o.data.update();(P/'review/limbs_v5').mkdir(exist_ok=True)
(P/'review/limbs_v5/mesh_edit.json').write_text(json.dumps({'changed_vertices':counts,'maximum_displacement_m':maxmove,'upper_radial_scale':1.55,'lower_radial_scale':1.65,'feet_radial_scale':1.70,'feet_length_scale':1.35,'approved_head_neck_preserved':True,'topology_uvs_weights_unchanged':True},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/limbs_v5_source.blend'));print(counts,maxmove)
