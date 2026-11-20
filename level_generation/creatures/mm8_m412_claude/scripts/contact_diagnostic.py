import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
sys.path.insert(0,str(P/'scripts'));import common
j=json.loads((P/'review/gates_preliminary/gates.json').read_text());glb=G.Glb(P/'export/pirate_gate_body.glb');mesh=G.load_meshes(glb)[0];cfg=json.loads((P/'gates_preliminary.json').read_text());r=G.Report(cfg);G.configure_mesh(mesh,cfg,r)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pirate_final.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Pirate'];pc=np.array([x.value for x in body.data.attributes['piece'].data]);co=np.array([v.co[:] for v in body.data.vertices]);reports=[]
for clip in ['Standing','Fidget','Attack']:
 for row in j['gates']:
  if row['clip']!=clip or row['lod']!='Pirate/colour0' or row['gate'] not in ['arm_body_penetration_mm','prop_body_penetration_mm'] or row['status']!='FAIL':continue
  side=row['region'];tm=row['time_s'];act=bpy.data.actions[clip];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(int(tm*120),subframe=tm*120%1)
  if side in 'LR':
   ix=np.where(mesh.contact_samples[side])[0][row['detail']['sample_vertex']];rest=mesh.rest[ix];vi=int(np.argmin(np.linalg.norm(co-rest,axis=1)));pose=glb.pose(next(a for n,a,s,e in glb.clips() if n==clip),np.array([tm]))[0];points=mesh.posed(pose);surface=mesh.surfaces[side].build(points);nearest=surface.tree.find_nearest(tuple(points[ix])) if hasattr(surface,'tree') else None
   reports.append({'clip':clip,'time':tm,'side':side,'piece':int(pc[vi]),'rest':rest.tolist(),'depth':row['worst'],'author_vertex':vi})
  common.workbench_clay(bpy.context.scene,True);common.render_views(str(P/'review'/f'contact_{clip}_{side}'),.85,2.15,views=('front','left','three_quarter'),resolution=(520,700))
print('CONTACT_DIAG',reports);(P/'review/contact_diagnostic.json').write_text(json.dumps(reports,indent=2))
