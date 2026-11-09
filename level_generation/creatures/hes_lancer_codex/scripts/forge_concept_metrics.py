"""Verify retained body geometry, rigid apron skinning, corpse continuity and plate motion."""
import bpy,sys,os,json,hashlib
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def body_digest(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Body'];h=hashlib.sha256()
 h.update(np.array([v.co[:] for v in o.data.vertices],np.float32).tobytes())
 h.update(json.dumps([[o.vertex_groups[e.group].name,float(e.weight)] for v in o.data.vertices for e in v.groups],separators=(',',':')).encode())
 h.update(json.dumps([list(p.vertices) for p in o.data.polygons],separators=(',',':')).encode());return h.hexdigest()
old=body_digest(P/'work/before_concept_20261024/forge_complete.blend');new=body_digest(P/'work/forge_final_clearance.blend');assert old==new,'Body geometry/weights changed'
r=bpy.data.objects['Rig'];sc=bpy.context.scene;obs=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Apron_')]
rest={o.name:np.array([v.co[:] for v in o.data.vertices]) for o in obs};edges={o.name:np.array([e.vertices[:] for e in o.data.edges]) for o in obs}
for o in obs:assert all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in o.data.vertices)
def pose(clip,frame):
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(frame),subframe=float(frame%1))
def points(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([list(o.matrix_world@p.co) for p in m.vertices]);ev.to_mesh_clear();return v
report={'body_geometry_and_named_weights_sha256':new,'body_unchanged':True,'roles':{}}
for role in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death','Dead'):
 a=bpy.data.actions['Forge_'+role];previous={};max_stretch=1.;max_jump=(0,None,None)
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
  pose(a.name,float(f))
  for o in obs:
   v=points(o);ix=edges[o.name];base=np.linalg.norm(rest[o.name][ix[:,0]]-rest[o.name][ix[:,1]],axis=1);ok=base>1e-6;ratio=np.linalg.norm(v[ix[:,0]]-v[ix[:,1]],axis=1)[ok]/base[ok];max_stretch=max(max_stretch,float(ratio.max()),float(1/ratio.min()))
   if o.name in previous:
    jump=float(np.linalg.norm(v.mean(0)-previous[o.name]));
    if jump>max_jump[0]:max_jump=(jump,o.name,float(f))
   previous[o.name]=v.mean(0)
 assert max_stretch<1.001,(role,max_stretch)
 report['roles'][role]={'apron_rigid_edge_ratio_max':max_stretch,'largest_half_frame_centroid_step_m':max_jump}
pose('Forge_Death',float(bpy.data.actions['Forge_Death'].frame_range[1]));held={b.name:b.matrix.copy() for b in r.pose.bones};pose('Forge_Dead',0)
error=max(float(np.max(np.abs(np.array(b.matrix)-np.array(held[b.name])))) for b in r.pose.bones);assert error<2e-4,error;report['death_to_dead_matrix_max_error']=error
(P/'review/forge_concept_preservation.json').write_text(json.dumps(report,indent=2)+'\n');print('CONCEPT_PRESERVATION',report,flush=True);sys.stdout.flush();os._exit(0)
