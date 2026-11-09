import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master_auto.blend'));C.reset();o=bpy.data.objects['Body'];report={}
for name,mi,job in [('head',1,'head_round3_texture_v2'),('hands',2,'hands_round3_texture')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/job/'model_urls_glb.glb'));src=max((x for x in set(bpy.data.objects)-before if x.type=='MESH'),key=lambda x:len(x.data.polygons));S=np.array([src.matrix_world@v.co for v in src.data.vertices]);polys=[f for f in o.data.polygons if f.material_index==mi];T=np.array([v.co[:]for v in o.data.vertices]);ids=sorted({i for f in polys for i in f.vertices});sub=T[ids];sc=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();S=S*sc+(sub.max(0)+sub.min(0))/2-(S.max(0)+S.min(0))*sc/2
 kd=KDTree(len(src.data.polygons))
 for f in src.data.polygons:kd.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 kd.balance();worst=0;uvdiff=0
 for f in polys:
  _,fi,dist=kd.find(Vector(T[list(f.vertices)].mean(0)));worst=max(worst,dist);sf=src.data.polygons[fi];assert len(sf.vertices)==len(f.vertices)
  for li,i in zip(f.loop_indices,f.vertices):
   j=int(np.argmin(np.linalg.norm(S[list(sf.vertices)]-T[i],axis=1)));uv=src.data.uv_layers.active.data[sf.loop_indices[j]].uv;uvdiff=max(uvdiff,(o.data.uv_layers.active.data[li].uv-uv).length);o.data.uv_layers.active.data[li].uv=uv
 assert worst<1e-4,(name,worst);report[name]={'matched_faces':len(polys),'worst_corner_centroid_m':worst,'original_uv_max_difference':uvdiff,'route':'Exact unreduced face/corner UV carry-over, no surface projection'}
 for ob in set(bpy.data.objects)-before:bpy.data.objects.remove(ob,do_unlink=True)
(P/'review/round3/uv_transfer.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/uv_master.blend'))
code=(P/'scripts/uv_raster.py').read_text()
for name,mi,N in [('head',1,1024),('hands',2,512)]:
 sys.argv=['uv_raster.py','--',str(P/'work/round3/uv_master.blend'),'UVMap',str(N)];text=code.replace('if bool(hd[t.polygon_index]) != want_head:','if me.polygons[t.polygon_index].material_index != '+str(mi)+':').replace("'work', f'uvraster_{layer}.npz'", "'work', 'round3', 'uvraster_"+name+".npz'");exec(compile(text,str(P/'scripts/uv_raster.py'),'exec'),{'__file__':str(P/'scripts/uv_raster.py'),'__name__':'__main__'})
