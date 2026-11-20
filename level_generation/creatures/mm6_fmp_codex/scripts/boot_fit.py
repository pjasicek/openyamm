"""Find grounded boot poses with their cut cuffs inside the open skirt hem."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/feedback_v3'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/feedback_drape.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];s=bpy.context.scene;m=o.data;piece=np.array([x.value for x in m.attributes['piece'].data]);rest=np.array([v.co[:] for v in m.vertices])
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(120)
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear()
clothfaces=[list(f.vertices) for f in m.polygons if piece[f.vertices[0]] in (1,7)];cb=BVHTree.FromPolygons(co,clothfaces)
pel=r.pose.bones['B_Pelvis'].head;feet=(r.pose.bones['B_L_Foot'].head+r.pose.bones['B_R_Foot'].head)/2;h=feet-pel;h.z=0;h.normalize();w=h.cross(Vector((0,0,1)));H=np.array(h);W=np.array(w)
hem=co[(piece==1)&(rest[:,2]<.108)];plane=float(np.median(hem@H));center=float(np.median(hem@W));fits={}
for part,side,sign in [(5,'L',1),(6,'R',-1)]:
 ids=np.where(piece==part)[0];idx={int(v):i for i,v in enumerate(ids)};faces=[[idx[v] for v in f.vertices] for f in m.polygons if piece[f.vertices[0]]==part];verts=co[ids];cuff=rest[ids,2]>.181
 foot=r.pose.bones[f'B_{side}_Foot'].head;toe=r.pose.bones[f'B_{side}_Toe0'].head;direction=toe-foot;direction.z=0;direction.normalize();yaw=direction.rotation_difference(h);anchor=np.array(foot);best=[]
 for pitch in np.arange(-60,61,3):
  Q=Quaternion(w,math.radians(float(pitch)))@yaw;rot=np.array(Q.to_matrix());v=(verts-anchor)@rot.T+anchor
  for depth in [.018,.03,.05,.075]:
   for span in [.065,.08,.095,.11]:
    shift=H*(plane-depth-np.max(v[cuff]@H))+W*(center+sign*span-np.mean(v[cuff]@W));shift[2]=.006-v[:,2].min();cv=v+shift
    overlaps=cb.overlap(BVHTree.FromPolygons(cv,faces))
    if not overlaps:best.append((abs(pitch)+depth*100+abs(span-.08)*100,float(pitch),depth,span,list(Q),shift.tolist(),float(cv[cuff,2].min()),float(cv[cuff,2].max())))
 assert best,(side,'no constrained boot fit')
 best.sort();fit=best[0];fits[side]={'pitch':fit[1],'cuff_depth':fit[2],'span':fit[3],'rotation':fit[4],'translation':fit[5],'anchor':anchor.tolist(),'cuff_z':fit[6:]};print('FIT',side,fits[side],flush=True)
 b=r.pose.bones[f'B_{side}_Calf'];Q=Quaternion(fit[4]);M=Q.to_matrix().to_4x4()@b.matrix;M.translation=Vector(anchor)+Q@(b.matrix.translation-Vector(anchor))+Vector(fit[5]);b.matrix=M;bpy.context.view_layer.update()
(R/'boot_fit.json').write_text(json.dumps(fits,indent=2));r.animation_data.action=None
sys.path.insert(0,str(P/'scripts'));import common
common.workbench_clay(s);s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.6,.6,.6);s.render.resolution_x=900;s.render.resolution_y=900
for n,eye,target,scale in [('feet',(0,1.08,4),(0,1.08,.1),.85),('side',(3,.4,.8),(0,.4,.2),1.8)]:
 cam=common.ortho_camera('probe',eye,(0,0,0),scale);cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam;s.render.filepath=str(R/f'boot_fitted_{n}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
