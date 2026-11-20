"""Move only the few liner samples with solid-angle-confirmed skin contact; millimetre fit finish."""
import bpy,sys,os,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];o=bpy.data.objects['hes_kept_collar'];sc=bpy.context.scene;pc=[v.value for v in b.data.attributes['piece'].data];fs=np.array([p.vertices[:]for p in b.data.polygons if pc[p.vertices[0]]==1]);move={};report=[]
def pts(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=[v.co.copy()for v in m.vertices];ev.to_mesh_clear();return p
for name,frame in [(name,float(f)) for name in ('Kept_Death','Kept_ClubR1') for f in np.arange(0,bpy.data.actions[name].frame_range[1]+.001,.5)]:
 r.animation_data.action=bpy.data.actions[name];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(int(frame),subframe=frame%1);bp=pts(b);tri=np.array(bp,dtype=float)[fs];tree=BVHTree.FromPolygons(bp,fs.tolist(),all_triangles=True);ps=pts(o);ids=[[v.index]for v in o.data.vertices]+[list(e.vertices)for e in o.data.edges]+[list(p.vertices)for p in o.data.polygons];inv=(r.pose.bones['Kept_Collar'].matrix@r.data.bones['Kept_Collar'].matrix_local.inverted()).inverted().to_3x3()
 for ix in ids:
  p=sum((ps[i]for i in ix),Vector())/len(ix);h,n,j,d=tree.find_nearest(p,.005)
  if h is None or d<.0001 or (p-h).dot(n)>-d*.5:continue
  a,c,e=(tri-np.array(p)).transpose(1,0,2);la=np.linalg.norm(a,axis=1);lc=np.linalg.norm(c,axis=1);le=np.linalg.norm(e,axis=1);num=np.einsum('ij,ij->i',a,np.cross(c,e));den=la*lc*le+np.einsum('ij,ij->i',a,c)*le+np.einsum('ij,ij->i',c,e)*la+np.einsum('ij,ij->i',e,a)*lc;w=np.arctan2(num,den).sum()/(2*np.pi)
  if abs(w)<.5:continue
  rest=sum((o.data.vertices[i].co for i in ix),Vector())/len(ix);delta=Vector((rest.x+.03255,rest.y-.034,0)).normalized()*.006;report.append({'clip':name,'frame':frame,'indices':ix,'depth_m':d,'shift_m':list(delta)})
  for i in ix:
   if i not in move or delta.length>move[i].length:move[i]=delta
print('CONTACTED_VERTICES',len(move),flush=True)
for i,d in move.items():o.data.vertices[i].co+=d
bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/'review/addons_v2/liner_fit_all.json').write_text(json.dumps({'vertices':len(move),'samples':report},indent=2)+'\n');print('LINER_FIT',len(move),report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
