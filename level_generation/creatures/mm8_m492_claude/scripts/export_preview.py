import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
for m in body.data.materials:
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.85;m.use_backface_culling=False
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(0)
for o in bpy.context.scene.objects:o.select_set(o in (rig,body,bpy.data.objects.get('MouthFire')))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(V/'dragon_animation.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
audit=json.loads((P/'work/clips.json').read_text());clips={}
for name,info in audit.items():
 frames=['m492sa0']+[f'm492w{c}0' for c in 'abcdefghij']
 if name in ('Attack','Cast'):frames=[f'm492a{c}0' for c in 'abcdefghij']
 if name=='Hit':frames=['m492sa0']+[f'm492n{c}0' for c in 'abcdefghi']
 if name=='Death':frames=['m492sa0']+[f'm492d{c}0' for c in 'abcdefghij']
 if name=='Dead':frames=['m492xa0']
 anchors=[{'time':i*.125,'label':str(i),'phase':'native pose','source_images':[f'../../references/native/{f}.png']} for i,f in enumerate(frames)]
 clips[name]={'label':name,'duration':info['duration'],'mode':'once' if name in ('Attack','Cast','Hit','Death') else 'loop','provenance':'Authored native-informed six-limb flight; breath release at the native 1.25 second impact.','anchors':anchors}
h=hashlib.sha256((V/'dragon_animation.glb').read_bytes()).hexdigest()
manifest={'revision':'animation-v2','model':'MM8 Dragon','default_clip':'Standing','default_model':'dragon','feedback':'../feedback/user_feedback.json','models':[{'id':'dragon','label':'Dragon animation review','url':'dragon_animation.glb?v='+h[:12],'sha256':h,'revision':'animation-v2'}],'clips':clips}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
