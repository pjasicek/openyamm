import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
for name,offset in [('bow',0),('arrow',.24)]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/f'export/mm6_arc1_{name}.glb'))
 obs=[o for o in bpy.data.objects if o not in before and o.type=='MESH'];assert len(obs)==1
 ob=obs[0];co=np.array([tuple(ob.matrix_world@v.co)for v in ob.data.vertices]);centre=(co.min(0)+co.max(0))/2
 # The split attachment is in bone-local coordinates; orient its real geometry for a neutral prop photograph.
 _,vec=np.linalg.eigh(np.cov(co.T));long=vec[:,-1];normal=vec[:,0]
 if long[np.argmax(abs(long))]<0:long=-long
 if name=='arrow':long=-long
 width=np.cross(long,normal);R=np.stack([normal,width,long]);ob.matrix_world=Matrix.Identity(4)
 for v,p in zip(ob.data.vertices,co):v.co=Vector(R@(p-centre))+Vector((0,offset,0))
bow=bpy.data.objects['Bow'];tip=np.array([tuple(v.co)for v in bow.data.vertices if v.co.z>.51]).mean(0)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.10,.10,.10,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
for name,pos,power,size in [('Key',(1,-1,1.2),75,2),('Fill',(-1,.8,.5),40,1.5),('Rim',(.3,.3,-1),20,1.3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
for name,direction,centre,scale,rez in [('bow_side',(1,0,0),(0,.10,0),1.40,(800,1200)),('bow_three_quarter',(1,-.6,.06),(0,.10,0),1.40,(800,1200)),('bow_grip',(1,-.6,.15),(0,0,0),.28,(1000,800)),('bow_nock',(1,-.4,.0),(0,.05,.54),.21,(900,800)),('arrow_head',(1,-.4,.1),(0,.24,.385),.15,(900,800))]:
 if name=='bow_nock':centre=tip
 d=Vector(direction).normalized();c=Vector(centre);cam=common.ortho_camera('ReviewCamera',c+d*3,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=rez;scene.render.filepath=str(P/f'review/{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
