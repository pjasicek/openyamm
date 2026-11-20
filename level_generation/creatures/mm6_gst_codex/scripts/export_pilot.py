import bpy,json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';V.mkdir(exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_v1.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body']
for ob in bpy.context.scene.objects:ob.select_set(ob in (r,o))
bpy.context.view_layer.objects.active=r;bpy.ops.export_scene.gltf(filepath=str(V/'pilot.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_all_influences=True,export_anim_slide_to_zero=True,export_attributes=False)
src=P.parent/'mm6_fmp_codex/review/viewer';html=(src/'index.html').read_text().replace('MM6 PeasantF2 3D Review','MM6 Ghost 3D Review').replace('MM6 PeasantF2 · town peasant','MM6 Ghost')
a=html.index('<header>');b=html.index('</header>',a);html=html[:a]+'<header><h1>MM6 Ghost · animation WIP</h1><p>Floating motion, native claw swipe, and cloth collapse. Use slow playback and the frame controls to inspect the model.</p>'+html[b:];html=html.replace('apron and cap colours','tabard and eye colours').replace('Apron / skirt','Lower shroud').replace('>Feet<','>Hem<');(V/'index.html').write_text(html);js=(src/'review.js').read_text().replace('mm6-fmp','mm6-gst').replace('MM6 PeasantF2','MM6 Ghost').replace('body:[0,.83,-.12,3.6], head:[0,1.51,.03,.67], arms:[0,1.05,0,2.0], shoulders:[0,1.27,0,1.1]', 'body:[0,1.10,-.10,4.4], head:[0,2.02,.03,.8], arms:[0,1.75,0,2.2], shoulders:[0,1.82,0,1.4]');(V/'review.js').write_text(js)
clips={};audit=json.loads((P/'work/animation_audit.json').read_text())
for name,info in audit.items():
 f='gstdief0' if name=='Dead' else 'gstdiea0' if name=='Death' else 'gstatka0' if name=='Attack' else 'gstwnca0' if name=='Hit' else 'gstflya0'
 clips[name]={'label':name,'duration':info['duration'],'mode':'loop' if name in ['Standing','Walking','Running'] else 'once','provenance':'Authored from MM6 Ghost sprites; owned GetHitF2 upper-body recoil.','anchors':[{'time':0,'label':'Native','phase':'reference','source_images':[f'../../../mm6_gst/native/{f}.png']}]}
(V/'manifest.json').write_text(json.dumps({'revision':'pilot_v4','model':'MM6 Ghost','default_clip':'Standing','default_model':'pilot','feedback':'feedback/user_feedback.json','models':[{'id':'pilot','label':'Clay motion pilot','url':'pilot.glb?v='+hashlib.sha256((V/'pilot.glb').read_bytes()).hexdigest()[:12]}],'clips':clips},indent=2))
(V/'feedback').mkdir(exist_ok=True);(V/'feedback/user_feedback.json').write_text('{"findings":[]}\n')
