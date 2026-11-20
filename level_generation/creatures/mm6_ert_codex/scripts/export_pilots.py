import bpy,json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_v6.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0)
for o in bpy.data.objects:o.select_set(o in (rig,body))
bpy.context.view_layer.objects.active=rig
out=P/'review/viewer';out.mkdir(exist_ok=True)
file=out/'mm6_ert_clay.glb'
bpy.ops.export_scene.gltf(filepath=str(file),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,
 export_reset_pose_bones=True,export_anim_slide_to_zero=True)
template=Path('level_generation/creatures/mm6_gar_codex/review/viewer')
html=(template/'index.html').read_text().replace('MM6 Gargoyle','MM6 Earth Elemental').replace('Stone / Marble / Diamond','Animation pilot')
a=html.index('<header>');b=html.index('</header>',a)+9
html=html[:a]+'<header><h1>MM6 Earth Elemental · animation pilot</h1><p>Clay rig review. Stone textures and final reduction follow the motion checks.</p></header>'+html[b:]
html=html.replace('Hands / claws','Hands / fists').replace('only skin colour and size differ in game','only stone colour differs in game')
(out/'index.html').write_text(html)
js=(template/'review.js').read_text().replace('mm6-gargoyle','mm6-earth-elemental').replace('MM6 Gargoyle','MM6 Earth Elemental').replace('body:[0,1.5,0,5.8]','body:[0,1.15,0,5.3]').replace('head:[0,1.7,0.05,1.1]','head:[0,2.1,0.05,1.35]').replace('arms:[0,1.2,0,2.5]','arms:[0,1.6,0,3.0]')
(out/'review.js').write_text(js)
sha=hashlib.sha256(file.read_bytes()).hexdigest()
clips={n:{'label':n,'duration':float(bpy.data.actions[n].frame_range[1]/30),'mode':'loop' if n in ['Standing','Walking'] else 'once','provenance':s,'anchors':[]} for n,s in [('Standing','Native quiet stone stance'),('Walking','Owned Mutant Walking adapted to native bent elbows'),('Attack','Native left rising fist with torso turn; impact 0.75 s')]}
manifest={'revision':'ert_pilot_v6','model':file.name,'model_sha256':sha,'default_model':'ert_clay','default_clip':'Attack','models':[{'id':'ert_clay','label':'Clay motion pilot','revision':'ert_pilot_v6','url':file.name,'sha256':sha}],'clips':clips,'feedback':'feedback/user_feedback.json'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'feedback').mkdir(exist_ok=True);(out/'feedback/user_feedback.json').write_text('{"findings":[]}')
