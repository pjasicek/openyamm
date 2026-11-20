from pathlib import Path
import bpy,sys,json,hashlib,struct
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/hands.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for obj in bpy.data.objects:obj.select_set(obj in (rig,body))
bpy.context.view_layer.objects.active=rig
out=p/'review/viewer';out.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out/'m488_preview.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_morph=False,export_skins=True)
raw=(out/'m488_preview.glb').read_bytes();doc=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
dur={a['name']:max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']};assert set(dur)=={'Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'},dur
sha=hashlib.sha256(raw).hexdigest()
manifest={'revision':'m488-animation-02','model':'m488_preview.glb','default_clip':'Standing','default_model':'pilot','model_sha256':sha,'feedback':'feedback/user_feedback.json','models':[{'id':'pilot','label':'Minotaur peasant · clay pilot','revision':'m488-animation-02','url':'m488_preview.glb?v='+sha[:12],'sha256':sha}],'clips':{}}
for name,seconds in dur.items():manifest['clips'][name]={'label':name,'duration':seconds,'mode':'once' if name in ('Attack','Hit','Fidget','Death') else 'loop','provenance':'Fitted local motion source; measured forward punch impact at 1.0 s; skirt has collision-fitted controls.','anchors':[]}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('PILOT_EXPORT',dur,sha)
