import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport_lod0.blend'));b=bpy.data.objects['Body'];k=bpy.data.objects['KnifeAsset'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
for ob in list(sc.objects):
 if ob not in [b,k,r]:bpy.data.objects.remove(ob,do_unlink=True)
common.setup_render((360,540))
sc.eevee.taa_render_samples=16
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.25,.25,.25,1);sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.6
for label,pos,power in [('key',(-3,-4,6),600),('fill',(4,0,4),450),('back',(0,4,3),450)]:
 data=bpy.data.lights.new(label,'AREA');data.energy=power;data.shape='DISK';data.size=4;light=bpy.data.objects.new(label,data);sc.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,.8))-light.location).to_track_quat('-Z','Y').to_euler()
sel=json.loads((P/'review/reduction_soft/selection.json').read_text())['0'];tex=Path(sel['textures'])
for mat in b.data.materials:
 stem='mfp_head'if 'Head'in mat.name else'mfp'
 if not mat.name.startswith('PeasantF3'):continue
 bs=mat.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(tex/f'{stem}_mfp_a.png'))
for name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];folder=P/'review/final_clips'/name;folder.mkdir(parents=True,exist_ok=True)
 for j,f in enumerate(np.linspace(0,a.frame_range[1],6)):
  sc.frame_set(int(f),subframe=float(f%1));lo,hi=common.world_bounds([b]);center=(lo+hi)/2;span=max(1.9,hi.z-lo.z+.2,(hi.y-lo.y)*1.55,(hi.x-lo.x)*1.55);common.render_views(str(folder/f'{j:02}'),center.z,span,views=('front','left','three_quarter'),resolution=(360,540),target=(center.x,center.y))
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0);common.render_views(str(P/'review/final_face'),1.48,.45,views=('front','left','three_quarter'),resolution=(720,720))
a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(19,subframe=.6875);H=r.pose.bones['B_R_Hand'].head;common.render_views(str(P/'review/final_grip'),H.z,.38,views=('front','left','three_quarter'),resolution=(720,720),target=(H.x,H.y))
b.hide_render=True;lo,hi=common.world_bounds([k]);center=(lo+hi)/2;common.render_views(str(P/'review/final_knife'),center.z,.36,views=('front','left','three_quarter'),resolution=(720,720),target=(center.x,center.y))

a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];b.hide_render=False
for frame,label in [(15.5,'windup'),(19.6875,'impact'),(26,'followthrough')]:
 sc.frame_set(int(frame),subframe=frame%1);lo,hi=common.world_bounds([b]);center=(lo+hi)/2;common.render_views(str(P/f'review/final_clips/Attack/{label}'),center.z,1.9,views=('front','left','three_quarter'),resolution=(360,540),target=(center.x,center.y));h=r.pose.bones['B_R_Hand'].head;common.render_views(str(P/f'review/round1/grip_{label}'),h.z,.29,views=('front','three_quarter'),resolution=(650,650),target=(h.x,h.y))
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0);common.render_views(str(P/'review/round1/skin_close'),1.21,.84,views=('front','three_quarter'),resolution=(720,720))
