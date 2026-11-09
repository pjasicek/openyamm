"""Keep accepted geometry; reparameterize body islands and cut the slow attack tail."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];W=P/'work/round2';R=P/'review/round2';sys.dont_write_bytecode=True
report={}
def arrays(ob):
 m=ob.data;m.calc_loop_triangles()
 return dict(co=np.array([v.co[:]for v in m.vertices]),normals=np.array([v.normal[:]for v in m.vertices]),tri=np.array([t.vertices[:]for t in m.loop_triangles]),uv=np.array([[m.uv_layers['UVMap'].data[i].uv[:]for i in t.loops]for t in m.loop_triangles]),mat=np.array([t.material_index for t in m.loop_triangles]),piece=np.array([v.value for v in m.attributes['piece'].data]))
def stats(a,size):
 out={}
 for mi in [0,1]:
  take=(a['mat']==mi);pp=a['co'][a['tri'][take]];uv=a['uv'][take];area=np.linalg.norm(np.cross(pp[:,1]-pp[:,0],pp[:,2]-pp[:,0]),axis=1)/2;ua=np.abs(np.cross(uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]))/2
  ok=area>1e-10;den=np.sqrt(ua[ok]*size[mi][0]*size[mi][1]/area[ok])/100;out[str(mi)]={'texels_cm_area_mean':float(np.sqrt(ua[ok].sum()*size[mi][0]*size[mi][1]/area[ok].sum())/100),'density_p10_p50_p90':np.percentile(den,[10,50,90]).tolist()}
 return out
# Source texture surface for rebaking the original 2K sari pattern without the old 1K round trip.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured.blend'));np.savez_compressed(W/'high_surface.npz',**arrays(bpy.data.objects['Body']))
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene;before=arrays(b)
 # Preserve every cut/wind-up key through frame 32; ease existing recovery to its frame-48 pose by frame 54.
 a=bpy.data.actions['Attack'];curves=[fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves];start=2/3;end=1.125;source_end=1.0
 for fc in curves:
  keep=[(float(k.co.x),float(k.co.y),k.interpolation)for k in fc.keyframe_points if k.co.x<=start*30]
  times=np.unique(np.r_[start,np.arange(math.ceil(start*240),int(end*240)+1)/240,end]);values=[]
  for t in times:
   u=(t-start)/(end-start);m=(end-start)/(source_end-start);v=(-2*u**3+3*u*u)+m*(u**3-2*u*u+u);source=start+(source_end-start)*v;values.append(float(fc.evaluate(source*30)))
  fc.keyframe_points.clear();fc.keyframe_points.add(len(keep)+len(times))
  for k,(x,y,interp)in zip(fc.keyframe_points,keep):k.co=(x,y);k.interpolation=interp
  for k,t,v in zip(list(fc.keyframe_points)[len(keep):],times,values):k.co=(t*30,v);k.interpolation='LINEAR'
  fc.update()
 a.use_frame_range=True;a.frame_start=0;a.frame_end=end*30
 if level==0:
  bm=bmesh.new();bm.from_mesh(b.data);uv=bm.loops.layers.uv['UVMap']
  for e in bm.edges:
   loops=e.link_loops
   e.seam=len(loops)!=2 or loops[0].face.material_index!=loops[1].face.material_index
   if len(loops)==2 and not e.seam:
    def coords(l):return {l.vert.index:tuple(round(v,6)for v in l[uv].uv),l.link_loop_next.vert.index:tuple(round(v,6)for v in l.link_loop_next[uv].uv)}
    e.seam=coords(loops[0])!=coords(loops[1])
  for face in bm.faces:face.select_set(face.material_index==0)
  bm.to_mesh(b.data);bm.free();bpy.ops.object.select_all(action='DESELECT');b.select_set(True);bpy.context.view_layer.objects.active=b
  bpy.context.scene.tool_settings.use_uv_select_sync=True;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.016);bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=True,margin_method='FRACTION',margin=32/4096);bpy.ops.object.mode_set(mode='OBJECT')
  for tri,old in zip(b.data.loop_triangles,before['uv']):
   if tri.material_index==1:
    for li,q in zip(tri.loops,old):b.data.uv_layers['UVMap'].data[li].uv=q
  after=arrays(b);report['before']=stats(before,[(1088,1024),(1024,1024)]);report['after']=stats(after,[(4096,4096),(1024,1024)])
  base_old=before;base_new=after
  # Lookup in the old parameter domain keeps existing LOD seams on the same islands.
  ids=np.flatnonzero(before['mat']==0);oldtri=before['uv'][ids];tree=BVHTree.FromPolygons([Vector((v[0],v[1],0))for tri in oldtri for v in tri],[(3*i,3*i+1,3*i+2)for i in range(len(ids))]);source_ids=ids
 else:
  m=b.data;m.calc_loop_triangles();uv=m.uv_layers['UVMap'].data
  for t in m.loop_triangles:
   if t.material_index!=0:continue
   old=np.array([uv[i].uv[:]for i in t.loops]);_,_,si,_=tree.find_nearest(Vector((*old.mean(0),0)));fi=source_ids[si];A=base_old['uv'][fi];C=base_new['uv'][fi];M=np.column_stack((A[1]-A[0],A[2]-A[0]));inv=np.linalg.pinv(M)
   for li,q in zip(t.loops,old):w=inv@(q-A[0]);uv[li].uv=C[0]+w[0]*(C[1]-C[0])+w[1]*(C[2]-C[0])
  after=arrays(b)
 # UV changes do not alter vertices, weights, topology or the held knife.
 assert np.array_equal(before['co'],after['co']) and np.array_equal(before['tri'],after['tri'])
 np.savez_compressed(W/f'mesh{level}.npz',**after,old_uv=before['uv'])
 r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'lod{level}.blend'));print('ROUND2_GEOMETRY',level,flush=True)
report['attack']={'preserved_until_s':start,'source_recovery_end_s':source_end,'new_duration_s':end,'impact_s':.65625};report['running']='Existing UnarmedRunForward2 arm swing and planted native-size gait retained; no RelaxRunForward'
(R/'authoring.json').write_text(json.dumps(report,indent=2))
