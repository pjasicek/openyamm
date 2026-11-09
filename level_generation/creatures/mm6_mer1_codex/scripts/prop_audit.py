import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:] if '--'in sys.argv else [];bpy.ops.wm.open_mainfile(filepath=str(P/(args[0]if args else'work/texture_upload_master.blend')));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['ClubMesh'];s=bpy.context.scene;me=body.data;pv=np.array([a.value for a in me.attributes['piece'].data]);faces=[tuple(f.vertices)for f in me.polygons]
# Keep exactly the four weights which the runtime consumes; audit this representation before reduction.
pruned=0
for o in [body,prop]:
 for v in o.data.vertices:
  weights=sorted([(g.group,g.weight)for g in v.groups if g.weight>1e-8],key=lambda x:-x[1]);pruned+=len(weights)>4;weights=weights[:4];total=sum(w for _,w in weights);assert total>0
  for g in v.groups[:]:o.vertex_groups[g.group].remove([v.index])
  for gi,w in weights:o.vertex_groups[gi].add([v.index],w/total,'REPLACE')
print('TOP4 pruned vertices',pruned,flush=True)
B=r.data.bones['Club'];axis=(B.tail_local-B.head_local).normalized();z=np.array([(v.co-B.head_local).dot(axis)for v in prop.data.vertices]);headids=np.where(z>.065)[0];G=json.loads((P/'work/grip_pose.json').read_text());report={}
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[o.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return co
for role in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];worst=0.;when=0.;low=1e9;rows=[]
 for t in np.arange(0,float(a.frame_range[1])/30+.0001,1/48):
  f=t*30;s.frame_set(int(f),subframe=float(f%1));co=coords(body);pc=coords(prop);tree=BVHTree.FromPolygons(co,faces);low=min(low,min(v.z for v in pc))
  for i in headids:
   loc,n,fi,d=tree.find_nearest(pc[i],.08)
   if loc is not None and (pc[i]-loc).dot(n)<-.7*d and d>worst:worst=d;when=float(t)
  h=np.array([tuple(pc[i])for i in headids]).mean(0);M=r.pose.bones['Club'].matrix;tip=M@B.matrix_local.inverted()@(B.head_local+axis*.452);root=M.translation;rows.append([float(t),*tip,*root])
 report[role]={'head_body_penetration_mm':worst*1000,'time':when,'lowest_club_m':low};(P/'review'/f'club_{role}_48hz.json').write_text(json.dumps(rows));print('PROP',role,report[role],flush=True)
(P/'review/prop_gate.json').write_text(json.dumps(report,indent=2));r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];s.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/prop_audited.blend'))
