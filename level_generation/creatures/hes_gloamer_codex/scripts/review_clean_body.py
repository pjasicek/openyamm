import bpy,sys,os,math
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/gloamer_clean_v1.blend'))
body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices])
out=P/'review/geometry/clean';out.mkdir(parents=True,exist_ok=True)
mat=bpy.data.materials.new('InspectionClay');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(0.45,0.48,0.5,1);bsdf.inputs['Roughness'].default_value=.8
me.materials.clear();me.materials.append(mat)
for poly in me.polygons:poly.use_smooth=True

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('Review');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for pos,power in [((3,-4,5),500),((-3,-2,3),300),((0,4,4),250)]:
    data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.size=4
    obj=bpy.data.objects.new('Softbox',data);scene.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector((0,0,.9))-obj.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.cameras.new('ReviewCamera');camera.type='ORTHO'
cam=bpy.data.objects.new('ReviewCamera',camera);scene.collection.objects.link(cam);scene.camera=cam
views=[(n,(0,0,.85),a,2.55,(640,640)) for n,a in [('front',0),('left',90),('back',180),('right',-90),('quarter',35)]]
views += [(n,(0,-.13,1.45),a,.68,(640,640)) for n,a in [('head_front',0),('head_side',90),('head_back',180)]]
for side,sg in [('L',1),('R',-1)]:
    hand=co[(co[:,0]*sg>co[:,0].max()*.73)&(co[:,2]<1.1)]
    centre=(hand.min(0)+hand.max(0))/2
    views += [(f'hand_{side}_{name}',tuple(centre),angle,.6,(640,640)) for name,angle in [('front',0),('back',180),('side',90*sg)]]
for name,target,angle,zoom,res in views:
    target=Vector(target);a=math.radians(angle);cam.location=target+Vector((5*math.sin(a),-5*math.cos(a),0))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camera.ortho_scale=zoom
    scene.render.resolution_x,scene.render.resolution_y=res;scene.render.filepath=str(out/f'{name}.png')
    bpy.ops.render.render(write_still=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
