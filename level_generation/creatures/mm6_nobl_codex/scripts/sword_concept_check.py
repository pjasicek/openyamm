"""Check sword contacts and compare floor clearance without changing the fitted animation."""
import bpy,numpy as np,json,runpy,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];out=p/'review/sword_concept_20261011';sys.path.insert(0,str(p/'scripts'))
sys.argv=['g6_sword_mesh.py','--',str(p/'export/mm6_nobl_runtime_lod0.glb')]
runpy.run_path(str(p/'scripts/g6_sword_mesh.py'),run_name='__main__')
report={}
for label,path in [('before',out/'before/mm6_nobl_lod0.glb'),('after',p/'export/mm6_nobl_lod0.glb')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
 r=next(o for o in bpy.data.objects if o.type=='ARMATURE');o=next(o for o in bpy.data.objects if o.type=='MESH' and o.parent==r)
 gi=o.vertex_groups['Sword'].index;bone=r.pose.bones['Sword'];inv=(r.matrix_world@bone.bone.matrix_local).inverted()
 points=[inv@(o.matrix_world@v.co) for v in o.data.vertices if any(g.group==gi and g.weight>.99 for g in v.groups)]
 points=[v for v in points if v.y>.061]
 result={}
 for a in bpy.data.actions:
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];minimum=1e9
  for f in np.arange(a.frame_range[0],a.frame_range[1]+1e-5,bpy.context.scene.render.fps/120):
   bpy.context.scene.frame_set(int(f),subframe=float(f%1));M=r.matrix_world@bone.matrix
   minimum=min(minimum,min((M@v).z for v in points))
  result[a.name]=minimum*1000
 report[label]=result
report['change_mm']={n:report['after'][n]-v for n,v in report['before'].items()}
assert all(report['after'][n]>=min(-1,report['before'][n]-.5) for n in list(report['after'])),report
(out/'blade_checks.json').write_text(json.dumps(report,indent=1));print('SWORD_FLOOR',json.dumps(report),flush=True)
