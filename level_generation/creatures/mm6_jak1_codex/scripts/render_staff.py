import bpy,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/staff_clay.blend'));staff=bpy.data.objects['Staff'];bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_jak1_runtime_lod0.glb'));mat=next(m for m in bpy.data.materials if m.name.startswith('HookedStaff_A'));staff.data.materials.clear();staff.data.materials.append(mat)
for p in staff.data.polygons:p.material_index=0
for o in list(bpy.data.objects):
 if o is not staff:bpy.data.objects.remove(o,do_unlink=True)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=40;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.render.image_settings.file_format='PNG';sc.world=bpy.data.worlds.new('Neutral studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
for name,pos,power,size in [('Key',(-1.5,-2,2.7),150,2),('Fill',(1.5,-1,1),65,2),('Rim',(.5,1.5,2.2),80,1.5)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
for name,direction,centre,scale,res in [('staff_closeup',(.3,-1,.07),(.05,0,.94),2.08,(650,1450)),('staff_hook',(0,-1,.06),(.06,0,1.70),.48,(1000,1000)),('staff_grip',(.5,-1,.2),(0,0,1.12),.35,(1000,1000))]:
 d=Vector(direction).normalized();c=Vector(centre);cam=common.ortho_camera('Camera',c+d*3,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.resolution_x,sc.render.resolution_y=res;sc.render.filepath=str(P/f'review/{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
