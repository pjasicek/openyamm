import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923')
s=bpy.data.scenes['MM6 Goblin Runtime 30K Export Check']
rows=[]
for o in s.objects:
 if o.type!='MESH':continue
 o.data.calc_loop_triangles();counts={'total':0,'belt_skirt_hip_region':0,'skirt_band_only':0}
 for t in o.data.loop_triangles:
  c=o.matrix_world @ (sum((o.data.vertices[i].co for i in t.vertices),Vector())/3)
  counts['total']+=1
  if abs(c.x)<.30 and -.21<c.z<.20:counts['belt_skirt_hip_region']+=1
  if abs(c.x)<.30 and -.21<c.z<.09:counts['skirt_band_only']+=1
 rows.append({'object':o.name,**counts})
report={'note':'Spatial centroid counts, not semantic face selection. Bands include underlying hips/thighs and pouch, exclude arms by x bound. Not an exact skirt-only count.','bounds':{'belt_skirt_hip_region':{'abs_x_max':.30,'z_min':-.21,'z_max':.20},'skirt_band_only':{'abs_x_max':.30,'z_min':-.21,'z_max':.09}},'objects':rows,'totals':{k:sum(row[k] for row in rows) for k in ('total','belt_skirt_hip_region','skirt_band_only')}}
(root/'runtime_candidate_30k/triangle_allocation_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['totals']))
