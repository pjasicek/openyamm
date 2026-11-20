import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack');out=ROOT/'review'
s=bpy.data.scenes['Meshy Goblin Sword and Native Attack'];bpy.context.window.scene=s;r=bpy.data.objects['MM6 Meshy Goblin Rig'];actions=json.loads(s['authored_actions'])
for o in s.objects:
 if o.type=='MESH' and o.find_armature()==r:
  for m in o.data.materials:
   if m.use_nodes:
    for n in m.node_tree.nodes:
     if n.type=='TEX_IMAGE' and n.image and n.image.name.startswith('texture_0') and 'metallic' not in n.image.name:m.node_tree.nodes.active=n
cam=s.camera;cam.data.type='ORTHO';cam.data.ortho_scale=2.65;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE';s.display.shading.show_cavity=True;s.display.shading.show_shadows=False;s.display.shading.background_type='WORLD';s.view_settings.view_transform='Standard'
jobs=[]
for view,vec in [('front',(0,-5,0)),('quarter',(-3,-5,0)),('side',(-5,0,0))]:
 for i,f in enumerate([1,4,7,10,13,16]):jobs.append(('Attack',f,view,vec,i))
jobs.append(('Standing',1,'standing',(0,-5,0),0))
def step():
 try:
  if not jobs:(out/'render_done.txt').write_text('complete');return None
  name,f,view,vec,i=jobs.pop(0);a=bpy.data.actions[actions[name]];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(f);target=Vector((0,0,1.10));cam.location=target+Vector(vec);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/f'{view}_{i:02}.png');bpy.ops.render.render(write_still=True);return .1
 except Exception:(out/'render_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.5);print('scheduled '+str(len(jobs))+' views')
