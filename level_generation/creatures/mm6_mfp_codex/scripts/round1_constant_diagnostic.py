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

r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
print('MODIFIERS',[(m.name,m.type)for m in b.modifiers],flush=True)
for mat in b.data.materials:
 if not mat.use_nodes:continue
 bs=mat.node_tree.nodes.get('Principled BSDF')
 if bs:
  for name in ['Base Color','Normal','Roughness','Metallic','Specular IOR Level']:
   for link in list(bs.inputs[name].links):mat.node_tree.links.remove(link)
  bs.inputs['Base Color'].default_value=(.3,.3,.3,1);bs.inputs['Roughness'].default_value=1;bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=0
for light in bpy.data.lights:light.use_shadow=False
common.render_views(str(P/'review/round1/diagnostic_constant'),1.15,.65,views=('front','three_quarter'),resolution=(650,650))
