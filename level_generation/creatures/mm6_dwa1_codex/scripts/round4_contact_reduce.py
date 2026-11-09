"""Protect the already sparse far-LOD tunic/covered trousers from contact-damaging collapse."""
import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
selection=json.loads((S.OUT/'selection.json').read_text());report={}
def cloth(blend,out):
 path=P/'scripts/skirt_intersections.py';source=path.read_text().replace("P/'work/export_reimport.blend'",f"Path({str(blend)!r})").replace("P/'review/skirt_intersections.json'",f"Path({str(out)!r})")
 exec(compile(source,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
 return json.loads(out.read_text())
for level in [2,3]:
 tag=f'body_lod{level}';curve=json.loads((S.OUT/f'{tag}_curve.json').read_text());source=P/f'work/round4/accepted_lod{level}.blend';base=cloth(source,S.OUT/tag/'accepted_cloth.json');trials=[]
 for step,ratio in enumerate([.9,.95,.975,1],1):
  bpy.ops.wm.open_mainfile(filepath=str(source));S.reset();body=bpy.data.objects['Body'];S.protect(body,'body')
  ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value in [2,5]]
  body.vertex_groups['_reduction_protect'].add(ids,1,'REPLACE')
  if ratio<1:S.reduce(body,ratio,planar=True)
  candidate=P/f'work/round4/body_lod{level}_contact{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate));r=cloth(candidate,S.OUT/tag/f'contact_attempt_{step}.json');worst=max(x['max_crossing_edges']for x in r.values())
  S.CALIBRATION.clear();S.CALIBRATION['diameter']=curve['camera']['bound_diameter_m'];folder=S.OUT/tag/f'contact_safe_{step}';S.render(folder,'body',level);metrics=S.evaluate(S.OUT/tag/'reference',folder)
  row={'step':f'contact_safe_{step}','collapse_ratio':ratio,'triangles':S.triangles(bpy.data.objects['Body']),'blend':str(candidate.relative_to(P)),'visual':metrics,'protected_cloth_vertices':len(ids),'max_crossing_edges':worst,'rig_gate_pass':worst==0};trials.append(row);print('CONTACT_REDUCE',level,ratio,row['triangles'],worst,metrics['min_iou'],metrics['min_ssim'],metrics['pass'],flush=True)
  if worst==0 and metrics['pass']:break
 else:raise AssertionError('No contact-safe reduction')
 selection['body'][level]=row
 for r in curve['steps']:
  if r['visual']['pass']:r['rig_gate_pass']=False;r['rig_failure']='Reduced covered trouser/tunic crossing; rejected in favour of contact-protected collapse.'
 curve['steps']+=trials;curve['accepted_max_cloth_crossing_edges']=max(x['max_crossing_edges']for x in base.values());(S.OUT/f'{tag}_curve.json').write_text(json.dumps(curve,indent=2)+'\n');report[tag]={'baseline_crossing_edges':curve['accepted_max_cloth_crossing_edges'],'trials':trials}
(S.OUT/'selection.json').write_text(json.dumps(selection,indent=2)+'\n');(S.OUT/'covered_contact.json').write_text(json.dumps(report,indent=2)+'\n')

