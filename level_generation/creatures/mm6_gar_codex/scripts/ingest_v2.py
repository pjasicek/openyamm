"""Verify full-creature return geometry and transfer only its improved body UVs."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,kdtree
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_source.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
targets=[bpy.data.objects[n] for n in ['Body','Head']];before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_texture_v2/model_urls_glb.glb'))
new=set(bpy.data.objects)-before;sources=[o for o in new if o.type=='MESH'];assert len(sources)==1
source=sources[0];S=np.array([source.matrix_world@v.co for v in source.data.vertices]);whole=np.vstack([np.array([v.co[:] for v in t.data.vertices]) for t in targets]);scale=np.ptp(whole,axis=0).max()/np.ptp(S,axis=0).max();offset=(whole.max(0)+whole.min(0)-scale*(S.max(0)+S.min(0)))/2;S=S*scale+offset
assert len(source.data.polygons)==sum(len(t.data.polygons) for t in targets)
tree=kdtree.KDTree(len(source.data.polygons))
for poly in source.data.polygons:tree.insert(Vector(S[list(poly.vertices)].mean(0)),poly.index)
tree.balance();used=set();report={};srcuv=source.data.uv_layers.active.data
for target in targets:
 T=np.array([v.co[:] for v in target.data.vertices]);maxerror=0;uv=target.data.uv_layers.active.data
 for poly in target.data.polygons:
  _,i,d=tree.find(Vector(T[list(poly.vertices)].mean(0)));assert i not in used;used.add(i);sp=source.data.polygons[i]
  for li in poly.loop_indices:
   pt=T[target.data.loops[li].vertex_index];sl=min(sp.loop_indices,key=lambda k:np.linalg.norm(S[source.data.loops[k].vertex_index]-pt));maxerror=max(maxerror,float(np.linalg.norm(S[source.data.loops[sl].vertex_index]-pt)))
   if target.name=='Body':uv[li].uv=srcuv[sl].uv
 assert maxerror<.0002,(target.name,maxerror)
 report[target.name]={'faces':len(target.data.polygons),'max_corner_error_m':maxerror,'uv_transferred':target.name=='Body'}
assert len(used)==len(source.data.polygons)
body=targets[0];mat=body.data.materials[0]
for node in mat.node_tree.nodes:
 if node.type=='TEX_IMAGE':node.image=bpy.data.images.load(str((P/'meshy/body_texture_v2/texture_urls_0_base_color.png').resolve()),check_existing=True)
body.data.calc_loop_triangles();uv=body.data.uv_layers.active.data;u=[];xyz=[];part=[]
for tr in body.data.loop_triangles:
 u.append([uv[li].uv[:] for li in tr.loops]);xyz.append([body.data.vertices[vi].co[:] for vi in tr.vertices]);wing=sum(sum(g.weight for g in body.data.vertices[vi].groups if body.vertex_groups[g.group].name.startswith('W_')) for vi in tr.vertices)/3;part.append(3 if wing>.35 else 1)
np.savez(P/'work/body_uv3d.npz',uv=np.array(u),xyz=np.array(xyz),part=np.array(part))
for o in new:bpy.data.objects.remove(o,do_unlink=True)
(P/'work/texture_correspondence_v2.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_source_v2.blend'))
common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(P/'review/textured_v2'),1.5,3.3,views=('front','left','back','three_quarter'),resolution=(900,1200));print('V2_TRANSFER',report)
