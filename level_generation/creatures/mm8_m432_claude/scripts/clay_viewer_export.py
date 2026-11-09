import bpy,json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
keep=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
sc.render.fps=30;r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
for o in bpy.data.objects:o.select_set(o.name in ['Rig','Body','SwordMesh'])
bpy.context.view_layer.objects.active=r
out=V/'mm8_m432_clay.glb';bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
raw=out.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);dur={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']};sha=hashlib.sha256(raw).hexdigest()
source={'Standing':'s','Walking':'w','Running':'w','Attack':'a','Cast':'a','Hit':'n','Death':'d','Dead':'d','Fidget':'f'}
m={'revision':'mm8_m432_clay_v1','model':out.name,'model_sha256':sha,'default_clip':'Standing','default_model':'m432_clay','feedback':'feedback/user_feedback.json','models':[{'id':'m432_clay','label':'Motion review','revision':'mm8_m432_clay_v1','url':out.name+'?v='+sha[:12],'sha256':sha}],'clips':{}}
for name,t in dur.items():
 m['clips'][name]={'label':name,'duration':t,'mode':'loop' if name in ('Standing','Walking','Running','Dead') else 'once','provenance':'Fitted local animation; native sprite shows character and action intent.','anchors':[{'time':0,'label':name,'phase':'Native action reference','source_images':[('../../../mm8_m432/references/identity_matte.png' if name=='Standing' else f'../../../mm8_m432/references/native_{source[name]}_v0_matte.png')]}]}
(V/'manifest.json').write_text(json.dumps(m,indent=1));print('CLAY EXPORT',dur)
