import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1/lod0.blend'));b=bpy.data.objects['Body'];k=bpy.data.objects['KnifeAsset'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
for ob in list(sc.objects):
 if ob not in [b,k,r]:bpy.data.objects.remove(ob,do_unlink=True)
common.setup_render((360,540))
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.25,.25,.25,1);sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.6
for label,pos,power in [('key',(-3,-4,6),600),('fill',(4,0,4),450),('back',(0,4,3),450)]:
 data=bpy.data.lights.new(label,'AREA');data.energy=power;data.shape='DISK';data.size=4;light=bpy.data.objects.new(label,data);sc.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,.8))-light.location).to_track_quat('-Z','Y').to_euler()
sel=json.loads((P/'review/reduction_soft/selection.json').read_text())['0'];tex=Path(sel['textures'])
for mat in b.data.materials:
 stem='mfp_head'if 'Head'in mat.name else'mfp'
 if not mat.name.startswith('PeasantF3'):continue
 bs=mat.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(tex/f'{stem}_mfp_a.png'))

for role,frame in [('Standing',0),('Hit',10),('Attack',13),('Attack',20),('Death',89.375)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(frame),subframe=frame%1);common.render_views(str(P/f'review/round1/latest_{role}_{frame:g}'),.85,1.9,views=('front','left'),resolution=(500,750))
 if role=='Attack':
  h=r.pose.bones['B_R_Hand'].head;common.render_views(str(P/f'review/round1/latest_grip_{frame:g}'),h.z,.3,views=('front','three_quarter'),resolution=(650,650),target=(h.x,h.y))
