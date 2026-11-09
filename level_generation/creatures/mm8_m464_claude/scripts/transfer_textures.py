"""Match both independent texture UV returns to the exact fitted master triangles."""
import bpy,sys,json,numpy as np,runpy
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();T=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);report={}
for label,slot in [('body',0),('head',1)]:
 before=set(bpy.data.objects);job=P/f'meshy/{label}_retexture_v1';bpy.ops.import_scene.gltf(filepath=str(job/'model_urls_glb.glb'));src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons));S=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices]);polys=[p for p in me.polygons if p.material_index==slot];ids=sorted({i for p in polys for i in p.vertices});sub=T if label=='body' else T[ids];scale=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+((sub.max(0)+sub.min(0))/2-(S.max(0)+S.min(0))*scale/2);tree=kdtree.KDTree(len(src.data.polygons))
 for p in src.data.polygons:tree.insert(Vector(S[list(p.vertices)].mean(0)),p.index)
 tree.balance();surface=BVHTree.FromPolygons([Vector(x) for x in S],[list(p.vertices) for p in src.data.polygons],all_triangles=True);patches=[];errors=[];suv=src.data.uv_layers.active.data;tuv=me.uv_layers.active.data;worst=0
 for p in polys:
  candidates=tree.find_n(Vector(T[list(p.vertices)].mean(0)),16);si=min((i for _,i,_ in candidates),key=lambda i:np.linalg.norm(T[list(p.vertices)][:,None]-S[list(src.data.polygons[i].vertices)][None,:],axis=2).min(axis=1).max());sp=src.data.polygons[si];assert len(sp.vertices)==len(p.vertices)==3
  distance=np.linalg.norm(T[list(p.vertices)][:,None]-S[list(sp.vertices)][None,:],axis=2).min(axis=1).max()
  if distance>.001:
   # Meshy altered two tiny scalp triangles; sample their nearest painted hair patch without changing anatomy.
   _,_,si,_=surface.find_nearest(Vector(T[list(p.vertices)].mean(0)));sp=src.data.polygons[si];a,b,c=[Vector(S[i]) for i in sp.vertices];v0=np.array(b-a);v1=np.array(c-a);basis=np.column_stack([v0,v1]);patch_error=0
   for li,vi in zip(p.loop_indices,p.vertices):
    q=closest_point_on_tri(Vector(T[vi]),a,b,c);error=(q-Vector(T[vi])).length;patch_error=max(patch_error,error);w=np.linalg.lstsq(basis,np.array(q-a),rcond=None)[0];coords=np.array([suv[i].uv[:] for i in sp.loop_indices]);tuv[li].uv=coords[0]*(1-w.sum())+coords[1]*w[0]+coords[2]*w[1]
   assert label=='head' and p.index in [11610,11613] and all(me.attributes['part'].data[i].value==6 for i in p.vertices) and patch_error<.003,(label,p.index,patch_error);patches.append({'face':p.index,'surface_error_m':patch_error});continue
  for li,vi in zip(p.loop_indices,p.vertices):
   distances=np.linalg.norm(S[list(sp.vertices)]-T[vi],axis=1);k=int(np.argmin(distances));worst=max(worst,float(distances[k]));errors.append((float(distances[k]),int(p.index),T[vi].tolist()));tuv[li].uv=suv[sp.loop_indices[k]].uv
 print('MATCH',label,scale,sorted(errors,reverse=True)[:5],flush=True)
 assert worst<.001,(label,worst);report[label]={'max_corner_error_m':worst,'matched_faces':len(polys),'scale':float(scale),'projected_tiny_faces':patches}
 for o in list(bpy.data.objects):
  if o not in before:bpy.data.objects.remove(o,do_unlink=True)
 mat=me.materials[slot];nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');im=nt.nodes.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(job/'texture_urls_0_base_color.png'));nt.links.new(im.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.8
(P/'work/uv_transfer.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
sys.path.insert(0,str(P.parent/'mm6_mfp_codex/scripts'));import common
rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0);common.workbench_clay(bpy.context.scene,True);common.render_views(str(P/'review/textured'),.84,1.9,views=('front','left','back','three_quarter'),resolution=(650,900))
