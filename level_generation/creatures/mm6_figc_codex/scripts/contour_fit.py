import bpy,bmesh,json,math,os,runpy,sys,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/round3';D=R/'contour_fit';D.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=D/'renders';C.O.mkdir(exist_ok=True);C.PHYSICAL=False;C.TIER_DIR=P/'work';cal=json.loads((R/'camera.json').read_text());center=Vector(cal['centres']['Body']);source=R/'outline_fit/lod3.blend';records=[]
for iteration in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['Rig'];act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0);bpy.context.view_layer.update();V=[];faces=[];mapping=[];fixed=[]
 for name in ['Body','Axe','Shield']:
  ob=bpy.data.objects[name];names=[g.name for g in ob.vertex_groups];matrices={b.name:rig.matrix_world@b.matrix@rig.data.bones[b.name].matrix_local.inverted()@rig.matrix_world.inverted()@ob.matrix_world for b in rig.pose.bones};grip=rig.matrix_world@rig.pose.bones['B_R_Hand' if name=='Axe' else 'B_L_Hand'].head;ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=[ob.matrix_world@v.co for v in me.vertices];offset=len(V);faces.extend([tuple(i+offset for i in f.vertices) for f in me.polygons]);ev.to_mesh_clear();V.extend(co)
  for v,p in zip(ob.data.vertices,co):
   M=Matrix(np.zeros((4,4)).tolist())
   for g in v.groups:M+=matrices[names[g.group]]*g.weight
   assert (M@v.co-p).length<.0001;mapping.append((ob.name,v.index,M.inverted()));fixed.append((name=='Body' and any(('Hand' in names[g.group] or 'Finger' in names[g.group]) and g.weight>.3 for g in v.groups)) or (name!='Body' and (p-grip).length<.13) or p.z<.025)
 me=bpy.data.meshes.new('contours');me.from_pydata(V,[],faces);bm=bmesh.new();bm.from_mesh(me);bm.normal_update();tree=BVHTree.FromBMesh(bm);edges=[];views=[];basis=[]
 for i in range(8):
  d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.08)).normalized();q=(-d).to_track_quat('-Z','Y');right=q@Vector((1,0,0));down=q@Vector((0,-1,0));basis.append([tuple(right),tuple(down)])
  for edge in bm.edges:
   ns=[f.normal.dot(d) for f in edge.link_faces]
   if len(ns)>1 and not min(ns)<=0<=max(ns):continue
   mid=(edge.verts[0].co+edge.verts[1].co)*.5;hit=tree.ray_cast(mid+d*4,-d,8)[0]
   if hit is None or (hit-mid).length>.003:continue
   normal=d.cross(edge.verts[1].co-edge.verts[0].co).normalized()
   if any(tree.ray_cast(mid+normal*(s*.003)+d*4,-d,8)[0] is None for s in [-1,1]):edges.append(tuple(v.index for v in edge.verts));views.append(i)
 bm.free();bpy.data.meshes.remove(me);np.savez(D/'fit_input.npz',V=np.array(V),edges=np.array(edges),views=np.array(views),basis=np.array(basis),center=np.array(center),fixed=np.array(fixed),scale=88/cal['body_diameter_m']);subprocess.run(['/usr/bin/python3',str(P/'scripts/fit_contours.py'),str(D)],check=True);out=np.load(D/'fit_output.npy')
 for p,(name,index,inverse) in zip(out,mapping):bpy.data.objects[name].data.vertices[index].co=inverse@Vector(p)
 for name in ['Body','Axe','Shield']:bpy.data.objects[name].data.update()
 source=D/f'iteration_{iteration}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(source));E=D/f'export_{iteration}';os.environ.update(FIGC_EXPORT_SOURCE=str(source),FIGC_EXPORT_DIR=str(E));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');folder=C.render(E/'mm6_figc_lod0.glb',3,f'iteration_{iteration}');mp=D/f'metrics_{iteration}.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'export_comparison/reference_lod3'),str(folder),str(mp)],check=True);m=json.loads(mp.read_text());pooled=sum(v['iou']*v['reference_foreground_pixels'] for v in m['views'])/sum(v['reference_foreground_pixels'] for v in m['views']);row={'iteration':iteration,'triangles':880,'minimum_iou':m['minimum_iou'],'pooled_iou':pooled,'fit':json.loads((D/'fit_report.json').read_text())};records.append(row);(D/'curve.json').write_text(json.dumps(records,indent=2));print('CONTOUR',row,flush=True)
