import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
for m in body.data.materials:
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.85;m.use_backface_culling=False
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(0)
for o in bpy.context.scene.objects:o.select_set(o in (rig,body))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(V/'phoenix_pilot.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
audit=json.loads((P/'work/clips.json').read_text());inv=json.loads((P/'references/native_inventory.json').read_text());actions=inv['bindings']['130']['actions'];clips={}
for name,info in audit.items():
 native={'Standing':'standing','Walking':'walk','Running':'walk','Fidget':'fidget','Attack':'attack','Cast':'attack','Hit':'hit','Death':'death','Dead':'corpse'}[name]
 source=actions[native]['views'];anchors=[];time=0
 for i,f in enumerate(source['0']):
  anchors.append({'time':time,'label':str(i),'phase':'native pose','source_images':['../../references/native/'+source[str(v)][i]['frame']+'.png' for v in range(5)]});time+=f['duration_ms']/1000
 if name in ('Attack','Cast'):anchors.append({'time':.875,'label':'Impact','phase':'native damage time','source_images':anchors[-1]['source_images']})
 clips[name]={'label':name,'duration':info['duration'],'mode':'once' if name in ('Attack','Cast','Hit','Death') else 'loop','provenance':'Local native-informed bird animation. Attack impact 0.875 s; native Hit 0.625 s. Death extends the observed back-fall into a physical landing.','anchors':anchors}
h=hashlib.sha256((V/'phoenix_pilot.glb').read_bytes()).hexdigest();manifest={'revision':'pilot-v1','model':'MM8 Phoenix','default_clip':'Standing','default_model':'phoenix','feedback':'../feedback/user_feedback.json','models':[{'id':'phoenix','label':'Phoenix motion pilot','url':'phoenix_pilot.glb?v='+h[:12],'sha256':h,'revision':'pilot-v1'}],'clips':clips}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
