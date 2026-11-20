"""Offline fit inspection only; the integrator owns the interactive viewer and game captures."""
import bpy,math,os,sys,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/overseer_assembly.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig']
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.world.color=(.17,.17,.17)
c=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',c);scene.collection.objects.link(cam);scene.camera=cam;c.type='ORTHO'
for name,pos,power,size in [('Key',(-2,-3,4),450,4),('Fill',(2,1,2),230,3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
motion=json.loads((P/'review/feedback_motion.json').read_text());melee=motion['Overseer_AttackMelee']
# Rank colour is previewed as a shader multiplier; runtime uses the same single texture through region ramps.
m=bpy.data.materials['OV_Sash'];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE');mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.5,.055,.024,1);nt.links.new(tex.outputs['Color'],mix.inputs[1]);nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
for name,clip,t,target,position,scale in [
 ('feedback_flight','Overseer_Flight',0,(0,0,1.05),(.8,-5,1.3),2.5),
 ('feedback_ranged','Overseer_AttackRanged',.45,(0,0,1.05),(.8,-5,1.3),2.5),
 ('feedback_windup','Overseer_AttackMelee',melee['windup_peak_s'],(0,0,1.1),(-1.4,-5,1.5),2.7),
 ('feedback_strike','Overseer_AttackMelee',41.5/48,(0,0,1.05),(-1.4,-5,1.5),2.7),
 ('feedback_followthrough','Overseer_AttackMelee',1.05,(0,0,1.05),(-1.4,-5,1.5),2.7)]:
 a=bpy.data.actions[clip];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 f=t*48;scene.frame_set(math.floor(f),subframe=f%1);cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();c.ortho_scale=scale;scene.render.filepath=str(P/'review'/f'{name}.png');bpy.ops.render.render(write_still=True)
# A short CPU-rendered playback exposes arm flailing that a single aim still cannot show.
a=bpy.data.actions['Overseer_AttackRanged'];rig.animation_data.action=a
if a.slots:rig.animation_data.action_slot=a.slots[0]
scene.render.resolution_x=scene.render.resolution_y=600;scene.cycles.samples=6
cam.location=(4,-5,1.7);cam.rotation_euler=(Vector((0,0,1.1))-cam.location).to_track_quat('-Z','Y').to_euler();c.ortho_scale=2.5
folder=P/'review/ranged_frames';folder.mkdir(exist_ok=True)
for i in range(31):
 t=i*.04;f=t*48;scene.frame_set(math.floor(f),subframe=f%1);scene.render.filepath=str(folder/f'{i:02d}.png');bpy.ops.render.render(write_still=True)
scene.render.resolution_x=scene.render.resolution_y=1000;scene.cycles.samples=12
# Review the two boss loadouts using the same bind transforms as the viewer exports.
a=bpy.data.actions['Overseer_Flight'];rig.animation_data.action=a
if a.slots:rig.animation_data.action_slot=a.slots[0]
scene.frame_set(0);cam.location=(-1.4,-5,1.5);cam.rotation_euler=(Vector((0,0,1.05))-cam.location).to_track_quat('-Z','Y').to_euler();c.ortho_scale=2.7
for variant in ['krav','ghulkat']:
 for part in ['collar_rod','arc_maul','plasma_saber','collar_key']:
  bpy.data.objects['OV_'+part].hide_render=part not in (['collar_rod','plasma_saber'] if variant=='krav' else ['arc_maul','collar_key'])
 for node in ['HipSaber','CollarKey','HolsterPistol']:bpy.data.objects['OV_'+node+'_hanger'].hide_render=(node!='HipSaber') if variant=='krav' else (node=='HipSaber')
 if variant=='ghulkat':
  pistol=bpy.data.objects['OV_pulse_pistol'];M=rig.data.bones['HolsterPistol'].matrix_local@rig.data.bones['PulsePistol'].matrix_local.inverted()
  for v in pistol.data.vertices:v.co=M@v.co
  pistol.vertex_groups['PulsePistol'].name='HolsterPistol';pistol.data.update()
 scene.render.filepath=str(P/'review'/f'feedback_{variant}.png');bpy.ops.render.render(write_still=True)
(P/'review/ranged_render.json').write_text(json.dumps({'assembly_sha256':hashlib.sha256((P/'work/overseer_assembly.blend').read_bytes()).hexdigest(),'clip':'Overseer_AttackRanged','frame_times_s':[round(i*.04,2) for i in range(31)],'method':'Blender Cycles CPU'},indent=2)+'\n')
print('ASSEMBLY_RENDER_DONE',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
