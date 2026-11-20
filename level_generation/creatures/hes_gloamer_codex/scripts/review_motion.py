import bpy,sys,os,math
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_animated.blend'))
body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices])
out=P/'review/motion_pilot';out.mkdir(parents=True,exist_ok=True)
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
rig=bpy.data.objects['Rig']
for action,frame in [('Standing',0),('Attack',11.5),('Hit',10.5),('Death',59.5),('Cast',22),('Running',10)]:
    act=bpy.data.actions[action];rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    scene.frame_set(int(frame),subframe=frame-int(frame))
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear()
    target=Vector((co.min(0)+co.max(0))/2)
    for name,angle in [('quarter',30),('left',90)]:
        a=math.radians(angle);cam.location=target+Vector((5*math.sin(a),-5*math.cos(a),0))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camera.ortho_scale=max(2.4,float(np.ptp(co,axis=0).max())*1.1)
        scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.filepath=str(out/f'{action}_{frame}_{name}.png')
        bpy.ops.render.render(write_still=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
