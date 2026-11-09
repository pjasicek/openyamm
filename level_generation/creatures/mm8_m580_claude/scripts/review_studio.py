"""Small fixed CPU studio for anatomy and deformation reviews."""
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

def render_views(mesh,prefix,views=None,bounds=None):
    co=np.array([v.co[:] for v in mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices])
    for obj in list(bpy.data.objects):
     if obj.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(obj,do_unlink=True)
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8
    sc.world=bpy.data.worlds.new('ClayWorld');sc.world.use_nodes=True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.38,.43,1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    for name,loc,power,size in [('Key',(1,-2,3),110,3),('Fill',(-2,-.5,1),65,3),('Rim',(0,2,2),75,2)]:
     light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));sc.collection.objects.link(light)
     light.location=loc;light.rotation_euler=(Vector((0,0,.15))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=power;light.data.shape='DISK';light.data.size=size
    mat=bpy.data.materials.new('Clay');mat.diffuse_color=(.4,.48,.53,1);mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=mat.diffuse_color;mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.6
    mesh.data.materials.clear();mesh.data.materials.append(mat)
    sc.render.resolution_x=800;sc.render.resolution_y=640;sc.render.resolution_percentage=100
    sc.render.film_transparent=True
    cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
    lo,hi=(co.min(0),co.max(0)) if bounds is None else (np.array(bounds[0]),np.array(bounds[1]));c=Vector((lo+hi)/2);extent=max(hi-lo);cam.data.ortho_scale=extent*1.44
    for name,d in [('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('top',(0,0,1)),('quarter',(1,-2,.25))]:
     if views and name not in views:continue
     direction=Vector(d).normalized();cam.location=c+direction*4*extent;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(Path(str(prefix)+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
