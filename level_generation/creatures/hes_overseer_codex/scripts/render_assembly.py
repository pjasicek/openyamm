"""Offline fit inspection only; the integrator owns the interactive viewer and game captures."""
import bpy,math,os,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/overseer_assembly.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig']
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.world.color=(.17,.17,.17)
c=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',c);scene.collection.objects.link(cam);scene.camera=cam;c.type='ORTHO'
for name,pos,power,size in [('Key',(-2,-3,4),450,4),('Fill',(2,1,2),230,3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
# Rank colour is previewed as a shader multiplier; runtime uses the same single texture through region ramps.
m=bpy.data.materials['OV_Sash'];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE');mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.5,.055,.024,1);nt.links.new(tex.outputs['Color'],mix.inputs[1]);nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
for name,clip,t,target,position,scale in [('assembly_front','Overseer_Flight',0,(0,0,1.05),(0,-5,1.2),2.4),('assembly_back','Overseer_Flight',0,(0,0,1.05),(0,5,1.2),2.4),('assembly_fire','Overseer_AttackRanged',.267,(0,0,1.05),(1,-4,1.3),2.4)]:
 a=bpy.data.actions[clip];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 f=t*48;scene.frame_set(math.floor(f),subframe=f%1);cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();c.ortho_scale=scale;scene.render.filepath=str(P/'review'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('ASSEMBLY_RENDER_DONE',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
