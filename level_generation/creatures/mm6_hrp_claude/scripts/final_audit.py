"""Audit the final three-atlas master at quarter-frame intervals."""
import bpy,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_hrp.blend'));sc=bpy.context.scene;body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];m=body.data
C=np.array([v.co[:] for v in m.vertices]);E=np.array([e.vertices[:] for e in m.edges]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);use=EL>.002
assert len(rig.data.bones)<=128
for v in m.vertices:
 w=[g.weight for g in v.groups if g.weight>1e-6];assert len(w)<=4 and abs(sum(w)-1)<1e-5
uv=m.uv_layers.active.data;areas=[[],[],[]]
for f in m.polygons:
 t=np.array([uv[i].uv[:] for i in f.loop_indices]);assert np.isfinite(t).all() and t.min()>-.001 and t.max()<1.001
 area=abs(float(np.linalg.det(np.stack([t[1]-t[0],t[2]-t[0]]))))/2
 if f.area>1e-10:areas[f.material_index].append(area/f.area)
report={'bones':len(rig.data.bones),'vertices':len(C),'triangles':len(m.polygons),'uv_area_per_surface_area':{s:np.percentile(a,[1,50,99]).tolist() for s,a in zip(['body','head','wings'],areas)},'clips':{}}
def coords():
 o=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=o.to_mesh();c=np.array([v.co[:] for v in mesh.vertices]);o.to_mesh_clear();return c
ends={}
for a in bpy.data.actions:
 rig.animation_data.action=a;lo,hi=a.frame_range;minimum=1e9;maxp99=0;maxedge=0;maxdelta=0;first=None;previous_legs={};max_leg_step=0;minimum_knee_separation=1e9
 for f in np.arange(lo,hi+.01,.25):
  sc.frame_set(int(f),subframe=float(f%1));c=coords();assert np.isfinite(c).all();first=c.copy() if first is None else first
  if a.name=='Attack':
   minimum_knee_separation=min(minimum_knee_separation,float((rig.pose.bones['LShin'].head-rig.pose.bones['RShin'].head).length))
   for n in ['LThigh','LShin','RThigh','RShin']:
    q=rig.pose.bones[n].matrix.to_quaternion()
    if n in previous_legs:
     angle=math.degrees(q.rotation_difference(previous_legs[n]).angle);angle=min(angle,360-angle)
     max_leg_step=max(max_leg_step,angle)
     assert angle<8,(a.name,f,n,'quarter-frame leg rotation',angle)
    previous_legs[n]=q
   # Knees must stay on their own side throughout the talon release.
   if 34<=f<=47:
    local=[rig.pose.bones['Root'].matrix.inverted()@rig.pose.bones[n].head for n in ['LShin','RShin']]
    assert local[0].x>local[1].x+.10,(f,'crossed knees',local)
  minimum=min(minimum,float(c[:,2].min()));length=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1);ratio=length[use]/EL[use];maxp99=max(maxp99,float(np.percentile(ratio,99)));maxedge=max(maxedge,float(ratio.max()));maxdelta=max(maxdelta,float((length-EL).max()))
 if a.name=='Attack':report['talon_continuity']={'max_quarter_frame_leg_rotation_degrees':max_leg_step,'minimum_knee_separation_m':minimum_knee_separation}
 loop=float(np.linalg.norm(c-first,axis=1).max());ends[a.name]=(first,c.copy())
 report['clips'][a.name]={'samples':round((hi-lo)*4)+1,'minimum_z':minimum,'edge_stretch_p99':maxp99,'edge_stretch_max_over_2mm':maxedge,'maximum_edge_extension_m':maxdelta,'endpoint_delta_m':loop}
 assert minimum>-.006,(a.name,minimum)
 if a.name in ['Standing','Walking','Running','Dead']:assert loop<.002
 if a.name=='Dead':
  torso=(abs(C[:,0]+.01)<.14)&(C[:,2]>1.01)&(C[:,2]<1.36)
  report['corpse']={'torso_min_z':float(c[torso,2].min()),'bounds_min':c.min(0).tolist(),'bounds_max':c.max(0).tolist(),'lowest_rest_point':C[np.argmin(c[:,2])].tolist()}
report['death_to_dead_error_m']=float(np.linalg.norm(ends['Death'][1]-ends['Dead'][0],axis=1).max());assert report['death_to_dead_error_m']<.002
(P/'review/checks').mkdir(exist_ok=True);(P/'review/checks/final_mesh_animation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
