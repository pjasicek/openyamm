import bpy,bmesh,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
out=p/'review/final_frames';out.mkdir(exist_ok=True);info=json.loads((p/'export/export_info.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'review/viewer/mm6_mep_a.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Mep'];sc=bpy.context.scene
common.workbench_clay(sc,True);sc.display.shading.show_specular_highlight=False;sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=False;sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
actions={a.name.split('|')[-1]:a for a in bpy.data.actions}
def pose(role,time):
 a=actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=time*sc.render.fps;sc.frame_set(int(f),subframe=f%1)
def shot(path,center,scale,view,resolution=(384,512)):
 angle=math.radians({'front':0,'left':90,'right':-90,'three_quarter':35,'back':180}[view]);d=Vector((math.sin(angle),-math.cos(angle),0));cam=common.ortho_camera('ReviewCamera',Vector(center)+d*6,(math.pi/2,0,angle),scale);sc.camera=cam;sc.render.resolution_x,sc.render.resolution_y=resolution;sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
records={}
for role,entry in info['clips'].items():
 duration=entry['duration'];times=[0,duration*.25,entry.get('impact',duration*.5),duration*.75,duration];bounds=[]
 for t in times:pose(role,t);bounds.append(common.world_bounds([body]))
 lo=Vector([min(b[0][i] for b in bounds) for i in range(3)]);hi=Vector([max(b[1][i] for b in bounds) for i in range(3)]);center=(lo+hi)/2
 for view in ['front','left','three_quarter']:
  angle=math.radians({'front':0,'left':90,'three_quarter':35}[view]);width=abs(math.cos(angle))*(hi.x-lo.x)+abs(math.sin(angle))*(hi.y-lo.y);scale=max(hi.z-lo.z,width/(384/512))*1.12
  for i,t in enumerate(times):pose(role,t);shot(out/f'{role}_{view}_{i}.png',center,scale,view)
 records[role]={'times':times,'views':['front','left','three_quarter']}
pose('Standing',0)
for view in ['front','left','three_quarter']:shot(out/f'face_{view}.png',(0,0,1.53),.44,view,(700,800))
for side in 'LR':
 center=rig.matrix_world@rig.pose.bones[f'B_{side}_Hand'].head
 center.z-=.018
 for view in ['front','left','right','back']:shot(out/f'hand_{side}_{view}.png',center,.29,view,(650,700))
# Extract the actual exported prop in the standing pose for isolated detail images.
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=bpy.data.meshes.new_from_object(ev);obj=bpy.data.objects.new('StaffReview',mesh);bpy.context.collection.objects.link(obj);obj.matrix_world=body.matrix_world.copy();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.delete(bm,geom=[f for f in bm.faces if 'Staff' not in mesh.materials[f.material_index].name],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(mesh);bm.free();body.hide_render=True;lo,hi=common.world_bounds([obj]);center=(lo+hi)/2
for view in ['front','three_quarter']:
 shot(out/f'staff_{view}.png',center,(hi-lo).length*1.1,view,(450,1100));shot(out/f'staff_detail_{view}.png',(center.x,center.y,1.15),.45,view,(700,900))
(p/'review/final_frames/index.json').write_text(json.dumps(records,indent=2))
