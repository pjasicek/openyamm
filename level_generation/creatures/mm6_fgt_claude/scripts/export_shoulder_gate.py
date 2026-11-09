"""Recheck the same armour surfaces after actual glTF export and import."""
from pathlib import Path
import bpy,sys,json,numpy as np
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from shoulder_intersections import intersections
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_revision2.blend'))
body=bpy.data.objects['Body'];pv=np.zeros(len(body.data.vertices),int);body.data.attributes['piece'].data.foreach_get('value',pv)
kd=KDTree(len(pv))
for v in body.data.vertices:kd.insert(body.matrix_world@v.co,v.index)
kd.balance()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_fgt_runtime_lod0.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Thug'))
me=body.data;me.calc_loop_triangles();parts=[]
for v in me.vertices:
 loc,i,d=kd.find(body.matrix_world@v.co);parts.append(int(pv[i]) if d<1e-5 else -1)
parts=np.array(parts);ids=np.where(parts==11)[0];si=np.where(parts==7)[0]
assert len(ids)>=60 and len(si)>=190,(len(ids),len(si))
def faces(ids):
 lookup={int(v):i for i,v in enumerate(ids)}
 return np.array([[lookup[v] for v in t.vertices] for t in me.loop_triangles if all(v in lookup for v in t.vertices)])
pf=faces(ids);sf=faces(si);assert len(pf)==99 and len(sf)>300,(len(pf),len(sf))
rows={};fps=bpy.context.scene.render.fps
for act in list(bpy.data.actions):
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];f0,f1=act.frame_range
 row={'samples':0,'crossings':[]}
 for f in np.arange(f0,f1+.0001,fps/192):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
  hits=intersections(co[si],sf,co[ids],pf);row['samples']+=1
  if hits:row['crossings'].append([float(f)/fps,len(hits)])
 rows[act.name]=row;print('EXPORT_SHOULDER',act.name,row,flush=True)
(p/'review/revision2/export_shoulder_gate.json').write_text(json.dumps({'sample_hz':192,'clips':rows},indent=2))
assert len(rows)==8 and all(not r['crossings'] for r in rows.values())
