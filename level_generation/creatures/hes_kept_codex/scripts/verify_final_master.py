"""Verify the final authoring bodies retain the gated weights, source frames and motion."""
import bpy,os,sys,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
def read(path,name):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects[name];r=bpy.data.objects['Rig'];data={'co':np.array([v.co[:] for v in o.data.vertices]),'faces':[tuple(p.vertices) for p in o.data.polygons],'weights':[[[o.vertex_groups[g.group].name,g.weight] for g in v.groups] for v in o.data.vertices],'bones':{b.name:([list(row) for row in b.matrix_local],b.parent.name if b.parent else None) for b in r.data.bones},'actions':{}}
 for a in bpy.data.actions:
  data['actions'][a.name]=sorted((f.data_path,f.array_index,[(list(k.co),list(k.handle_left),list(k.handle_right),k.interpolation) for k in f.keyframe_points]) for l in a.layers for s in l.strips for cb in s.channelbags for f in cb.fcurves if 'Kept_Collar' not in f.data_path)
 return data
report={}
for kind,style in [('male','ragged'),('male','freed'),('female','freed')]:
 original=read(P/'work'/kind/'rig_final_done.blend','Body');final=read(P/'work'/kind/f'runtime_{style}.blend','Kept');moved=np.where(np.linalg.norm(original['co']-final['co'],axis=1)>1e-7)[0]
 assert original['faces']==final['faces'] and original['weights']==final['weights']
 for name,value in original['bones'].items():assert final['bones'][name]==value,name
 for name,curves in final['actions'].items():
  expected=original['actions'][name]
  if kind=='male' and style=='ragged' and name in ('Kept_Death','Kept_ArmedDeath'):
   curves=[f for f in curves if f[0]!='pose.bones[\"B_Pelvis\"].location'];expected=[f for f in expected if f[0]!='pose.bones[\"B_Pelvis\"].location']
   assert json.loads((P/'review/equipped_death_floor.json').read_text())['pass']
  assert curves==expected,name
 if kind=='female':assert set(map(int,moved))==set(json.loads((P/'review/female/hairline_repair.json').read_text())['moved_vertex_ids'])
 else:assert len(moved)==0
 report[kind+'_'+style]={'pass':True,'retained_gated_bones':len(original['bones']),'matched_body_actions':len(final['actions']),'moved_vertices':len(moved),'max_vertex_move_m':float(np.linalg.norm(original['co']-final['co'],axis=1).max()),'only_exception':'female hair-cap fit; collider skin and limbs unchanged' if kind=='female' else ('separate collar keys; rigid world-Z floor lift during two death clips (equipped_death_floor.json)' if style=='ragged' else 'none')}
(P/'review/final_master_invariance.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL_INVARIANCE',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
