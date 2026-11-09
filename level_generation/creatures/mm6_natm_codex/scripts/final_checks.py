import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
# Surface-interior cloth samples supplement the shared leg-in-panel runtime test.
code=(P/'scripts/contact_audit.py').read_text().replace('work/contact_master.blend','work/runtime_lod0.blend').replace("'review/contact_audit.json'","'review/final_cloth_surface.json'")
code=code.replace("row['body_min_z']=min(row['body_min_z'],float(v[pv==0,2].min()))","row['body_min_z']=min(row['body_min_z'],float(v[pv==0,2].min()))\n  if float(v[:,2].min())<row.get('all_geometry_min_z',1e9):row.update(all_geometry_min_z=float(v[:,2].min()),lowest_piece=int(pv[np.argmin(v[:,2])]),lowest_frame=float(f))")
code=code.replace("for act in bpy.data.actions:","props={}\nfor act in bpy.data.actions:\n if act.name not in ['Death','Hit','Running']:continue")
exec(compile(code,str(P/'scripts/contact_audit.py'),'exec'),{'__name__':'__main__','__file__':str(P/'scripts/contact_audit.py')})
import json
f=P/'review/final_cloth_surface.json';record=json.loads(f.read_text());record.pop('grip_exclusion_m',None);record.pop('buckler_shell_only',None);record['scope']='Cloth-to-skin interior samples; props are checked by the shared runtime gates.'
for row in record['clips'].values():
 for key in ['spear_body_penetration_m','buckler_shell_penetration_m','prop_min_z']:row.pop(key,None)
f.write_text(json.dumps(record,indent=2))
runpy.run_path(str(P/'scripts/review_stage.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/final_render.py'),run_name='__main__')
