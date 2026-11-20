"""Offline CPU clay diagnostics; no browser, desktop, game or shared Blender scene."""
import bpy, sys, math, json
from pathlib import Path
from mathutils import Vector
import numpy as np
P=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
blend=args[0] if args else 'work/raw_geometry.blend'
prefix=args[1] if len(args)>1 else 'review/raw'
bpy.ops.wm.open_mainfile(filepath=str(P/blend))
sc=bpy.context.scene
if len(args)>4:
 rig=bpy.data.objects['Rig'];rig.animation_data_create();rig.animation_data.action=bpy.data.actions[args[3]]
 if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 frame=float(args[4]);sc.frame_set(int(frame),subframe=frame-int(frame))
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12
sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.world=bpy.data.worlds.new('DiagnosticWorld');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(0.25,0.28,0.32,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=0.8
for o in list(sc.objects):
 if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
meshes=[o for o in sc.objects if o.type=='MESH']
co=np.concatenate([np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]) for o in meshes])
lo,hi=co.min(0),co.max(0);c=Vector((lo+hi)/2);ext=float((hi-lo).max())
if len(args)>2 and args[2]=='upper':c=Vector((-0.6,0.5,3.0));ext=3.2
if len(args)>2 and args[2].startswith('hand'):
 side=args[2][-1];j=json.loads((P/'work/joints.json').read_text())['joints'];c=Vector(j[side+'_Hand'])+Vector((.15,-.25,-.25));ext=1.35
for j,(direction,energy) in enumerate([((2,-3,5),250),((-3,1,2),150)]):
 data=bpy.data.lights.new('Area'+str(j),'AREA');data.energy=energy*ext**2;data.shape='DISK';data.size=ext*3
 ob=bpy.data.objects.new(data.name,data);sc.collection.objects.link(ob);ob.location=c+Vector(direction)*ext
 ob.rotation_euler=(c-ob.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('DiagnosticCamera',bpy.data.cameras.new('DiagnosticCamera'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=ext*1.15
views={'front':(0,-4,0.2),'side':(4,0,0.2),'back':(0,4,0.2),'top':(0,0,4),'q34':(3,-4,2)}
for name,d in views.items():
 cam.location=c+Vector(d)*ext;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
 sc.render.filepath=str(P/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
