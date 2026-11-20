"""Measure smaller body/head maps against the same accepted close-up before choosing their resolution."""
import bpy,json,sys,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';source=R/'protected_axe/export_lod0';sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
reports=[]
for label,body_size,head_size in [('maps_1k',1024,1024),('head_1k',2048,1024),('head_2016',2048,2016)]:
 D=R/label;E=D/'export_lod0';T=E/'textures';T.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(source/'rebaked_authoring.blend'))
 for suffix,size in [('',body_size),('_head',head_size),('_gear',2048)]:
  for kind in ['basecolor','normal','metal_rough','region_mask']:
   filename=f'figc{suffix}_{kind}.png' if kind=='region_mask' else f'figc{suffix}_{kind}_{"2k" if suffix=="_gear" else "1k"}.png';image=bpy.data.images.get(f'rebake{suffix}_{kind}')
   if image is None:image=bpy.data.images.load(str(source/'textures'/filename));image.colorspace_settings.name='sRGB' if kind=='basecolor' else 'Non-Color'
   if tuple(image.size)!=(size,size):image.scale(size,size)
   image.filepath_raw=str(T/filename);image.file_format='PNG';image.save();image.pack()
 shutil.copy2(source/'textures/figc_ramps.json',T/'figc_ramps.json');bpy.ops.wm.save_as_mainfile(filepath=str(E/'rebaked_authoring.blend'));rig=bpy.data.objects['Rig'];target=bpy.data.objects['FighterChain']
 for o in bpy.data.objects:o.select_set(o in [rig,target])
 bpy.context.view_layer.objects.active=rig;rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 bpy.ops.export_scene.gltf(filepath=str(E/'rebaked.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 subprocess.run(['/usr/bin/python3',str(P/'scripts/rebake_review_materials.py'),str(T)],check=True);C.O=D/'physical';C.O.mkdir(exist_ok=True);C.PHYSICAL=True;C.TIER_DIR=T;out=C.render(E/'rebaked.glb',0,'rebaked');mp=D/'metrics.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'rebake/physical/reference_lod0'),str(out),str(mp)],check=True);metrics=json.loads(mp.read_text());row={'label':label,'body_px':body_size,'head_px':head_size,'source':str(E.relative_to(P)),'metrics':metrics};reports.append(row);(R/'texture_resolution_curve.json').write_text(json.dumps(reports,indent=2))
 if metrics['pass']:(R/'final_texture_choice.json').write_text(json.dumps(row,indent=2));break
else:raise RuntimeError('No compact texture candidate met the unchanged close-up thresholds')
