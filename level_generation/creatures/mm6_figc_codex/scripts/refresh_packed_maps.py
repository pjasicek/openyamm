"""Relink saved compact images explicitly, then verify the exact embedded normal/basecolour maps."""
import bpy,json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';choice=json.loads((R/'final_texture_choice.json').read_text());E=P/choice['source'];T=E/'textures';bpy.ops.wm.open_mainfile(filepath=str(E/'rebaked_authoring.blend'));body=bpy.data.objects['FighterChain'];rig=bpy.data.objects['Rig']
for mat in body.data.materials:
 s='_head' if 'Head' in mat.name else '_gear' if 'Gear' in mat.name else '';size='2k' if s=='_gear' else '1k';nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
 def fresh(kind):
  image=bpy.data.images.load(str(T/f'figc{s}_{kind}_{size}.png'),check_existing=False);image.colorspace_settings.name='sRGB' if kind=='basecolor' else 'Non-Color';image.pack();node=nt.nodes.new('ShaderNodeTexImage');node.image=image;return node
 nt.links.new(fresh('basecolor').outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(fresh('normal').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(fresh('metal_rough').outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
bpy.ops.wm.save_as_mainfile(filepath=str(E/'rebaked_authoring.blend'))
for o in bpy.data.objects:o.select_set(o in [body,rig])
bpy.context.view_layer.objects.active=rig;rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.ops.export_scene.gltf(filepath=str(E/'rebaked.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=R/choice['label']/'physical';C.PHYSICAL=True;C.TIER_DIR=T;out=C.render(E/'rebaked.glb',0,'rebaked');mp=R/choice['label']/'metrics.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'rebake/physical/reference_lod0'),str(out),str(mp)],check=True);choice['metrics']=json.loads(mp.read_text());assert choice['metrics']['pass'];choice['packed_images_refreshed']=True;(R/'final_texture_choice.json').write_text(json.dumps(choice,indent=2))
# Baseline far-LOD comparison at the same corrected switch size.
C.O=R/'switch_height';C.cal['body_diameter_m']=1.763883397;C.TIER_DIR=R/'reference_tier_textures';d,raw=C.read_glb(R/'before/export/mm6_figc_lods.glb');node=next(n for n in d['nodes'] if n.get('name')=='FighterChain');node['mesh']=d['meshes'][node['mesh']]['extras']['openyamm_lods'][2];path=C.O/'installed_lod3.glb';C.write_glb(path,d,raw);out=C.render(path,3,'installed');subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(C.O/'reference_lod3'),str(out),str(R/'installed_lod3_metrics.json')],check=True)
