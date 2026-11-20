from pathlib import Path
import bpy,bmesh,numpy as np,json,sys
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_fitted.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];path=json.loads((p/'work/boulder_path.json').read_text())
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/'meshy/boulder_v1/model_urls_glb.glb'));new=set(bpy.data.objects)-before
rock=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.polygons));import boulder_mesh;boulder_mesh.prepare(rock)
for o in new:
 if o!=rock:bpy.data.objects.remove(o,do_unlink=True)
bm=bmesh.new();bm.from_mesh(rock.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.normal_update();print('WELDED',len(bm.verts),len(bm.faces),'boundary',sum(e.is_boundary for e in bm.edges),'volume',bm.calc_volume(signed=True),flush=True)
tree=BVHTree.FromBMesh(bm)
def signed(v):
 hit,n,face,d=tree.find_nearest(Vector(v));return d if (Vector(v)-hit).dot(n)>=0 else -d
common.workbench_clay(bpy.context.scene)
for f in [12,24]:
 a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);snapshot={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=snapshot[pb.name]
 bpy.context.view_layer.update();centre=Vector(path[f]['centre']);rock.location=centre
 common.render_views(str(p/f'review/contact_raw_{f}'),centre.z,.95,views=('front','left','three_quarter'),target=(0,centre.y),resolution=(800,800))
 for side,sign in [('L',1),('R',-1)]:
  hn=f'B_{side}_Hand';h=rig.data.bones[hn];kn=sum((rig.data.bones[f'B_{side}_Finger{i}'].head_local for i in range(1,5)),Vector())/4;fw=kn-h.head_local
  ids=[v.index for v in body.data.vertices if .2<(v.co-h.head_local).dot(fw)/fw.length_squared<.95 and any(g.group==body.vertex_groups[hn].index and g.weight>.55 for g in v.groups)]
  for iteration in range(3):
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();points=np.array([mesh.vertices[i].co-centre for i in ids]);ev.to_mesh_clear();ds=np.array([signed(v) for v in points]);j=ds.argmin();axis=np.array([sign*.94,0,-.34]);dhi=min(signed(v) for v in points+.09*axis)
   print('PALM',f,side,iteration,len(ids),'bbox',points.min(0),points.max(0),'deep',ds[j],points[j],'dhi',dhi,flush=True)
   lo,hi=-.09,.09
   for k in range(12):
    mid=(lo+hi)/2
    if min(signed(v) for v in points+mid*axis)<.001:lo=mid
    else:hi=mid
   shift=(lo+hi)/2;M=armik.W(rig,hn);target=M.translation+Vector(axis*shift);pole=armik.W(rig,f'B_{side}_Forearm').translation.copy();reach=armik.solve(rig,side,target,pole=pole,hand_rot=M.to_3x3())
   print('SHIFT',shift,'reach',reach,'target_error',(armik.W(rig,hn).translation-target).length,flush=True)
 common.render_views(str(p/f'review/contact_shift_{f}'),centre.z,.95,views=('front','left','three_quarter'),target=(0,centre.y),resolution=(800,800))
