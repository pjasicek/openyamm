"""Copy only returned UVs by bijective triangle/corner correspondence; retain the gated rig."""
import bpy,sys,os,json
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_texturing.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
co=np.array([body.matrix_world@v.co for v in me.vertices]);fa=np.array([p.vertices[:] for p in me.polygons]);head=np.array([a.value for a in me.attributes['head'].data],bool)
pc=np.array([a.value for a in me.attributes['piece'].data]);report={};layouts={}
for suffix,layername in [('body','BodyUV'),('head','HeadUV')]:
 job=f'retexture_{suffix}_v1';before=set(bpy.data.objects)
 bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/job/'model_urls_glb.glb'))
 added=set(bpy.data.objects)-before;obs=[o for o in added if o.type=='MESH'];assert len(obs)==1
 o=obs[0];m=o.data;m.calc_loop_triangles();v=np.array([o.matrix_world@x.co for x in m.vertices]);fs=np.array([t.vertices[:] for t in m.loop_triangles]);uv=np.array([m.uv_layers.active.data[li].uv[:] for t in m.loop_triangles for li in t.loops]).reshape(-1,3,2)
 sel=np.where(head)[0] if suffix=='head' else np.arange(len(fa));target=co[fa[sel]].reshape(-1,3)
 scale=float(np.linalg.norm(np.ptp(target,axis=0))/np.linalg.norm(np.ptp(v,axis=0)));shift=(target.min(0)+target.max(0))/2-scale*(v.min(0)+v.max(0))/2
 v=v*scale+shift;cent=v[fs].mean(1);tree=KDTree(len(cent))
 for i,c in enumerate(cent):tree.insert(c,i)
 tree.balance();assigned=[];worst=0.;out=np.zeros((len(fa),3,2))
 assert len(fs)==len(sel),(job,len(fs),len(sel))
 for fi in sel:
  tri=co[fa[fi]];_,j,d=tree.find(tri.mean(0));assigned.append(j);q=v[fs[j]];ix=np.linalg.norm(tri[:,None]-q[None],axis=-1).argmin(1)
  assert len(set(ix))==3
  dist=np.linalg.norm(tri-q[ix],axis=1).max();worst=max(worst,float(dist));out[fi]=uv[j,ix]
 assert len(set(assigned))==len(sel),(job,'nonbijective')
 assert worst<2e-5,(job,'geometry changed',worst)
 layer=me.uv_layers.get(layername) or me.uv_layers.new(name=layername)
 for fi in sel:
  for li,value in zip(me.polygons[int(fi)].loop_indices,out[fi]):layer.data[li].uv=value
 layouts[layername]=out
 report[job]={'triangles':len(sel),'bijective':True,'worst_corner_error_m':worst,'returned_uniform_scale':scale,'translation_m':shift.tolist()}
 for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
np.savez_compressed(P/'texturing'/'gloamer_uv.npz',vertices=co,faces=fa,head=head,piece=pc[fa[:,0]],**layouts)
(P/'review/returned_uv_transfer.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
print('TRANSFER',report,flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
