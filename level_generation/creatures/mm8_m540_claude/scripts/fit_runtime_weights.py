"""Enforce the renderer's eight-influence limit and measure every affected vertex through all actions."""
from pathlib import Path
import bpy,json,os,runpy,numpy as np
p=Path(__file__).resolve().parents[1];blend=p/'work/rig_uv.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
rows={v.index:sorted([(e.group,e.weight) for e in v.groups if e.weight>0],key=lambda x:-x[1]) for v in body.data.vertices}
ids=[i for i,row in rows.items() if len(row)>8];cache=[];max_before=max(map(len,rows.values()))
def points():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([tuple(m.vertices[i].co) for i in ids]);ev.to_mesh_clear();return P
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in np.arange(0,a.frame_range[1]+.001,.5):
  scene.frame_set(int(f),subframe=float(f-int(f)));cache.append((a.name,float(f),points()))
for i in ids:
 row=rows[i][:8];total=sum(w for _,w in row)
 for g in body.vertex_groups:g.remove([i])
 for group,w in row:body.vertex_groups[group].add([i],w/total,'REPLACE')
worst={'error_m':0};dropped=max((sum(w for _,w in rows[i][8:]) for i in ids),default=0)
for name,f,before in cache:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(int(f),subframe=f-int(f));after=points()
 if ids:
  delta=np.linalg.norm(after-before,axis=1);i=int(np.argmax(delta))
  if delta[i]>worst['error_m']:worst={'error_m':float(delta[i]),'clip':name,'frame':f,'vertex':ids[i]}
assert worst['error_m']<.001,worst
assert max(sum(e.weight>0 for e in v.groups) for v in body.data.vertices)<=8
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report={'before_max_influences':max_before,'after_max_influences':8,'affected_vertices':len(ids),'max_discarded_weight':dropped,'max_pose_error':worst}
(p/'work/runtime_weights.json').write_text(json.dumps(report,indent=2)+'\n');print('RUNTIME_WEIGHTS',report,flush=True)
os.environ['MAGE_BLEND']=str(blend);os.environ['MAGE_CHECK_STAGE']='runtime'
runpy.run_path(str(p/'scripts/check_full_actions.py'),run_name='__main__')
