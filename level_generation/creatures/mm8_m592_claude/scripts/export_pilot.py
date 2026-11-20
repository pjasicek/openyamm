"""Export the Guardian clay pilots and shared review manifest without changing the animation master."""
from pathlib import Path
import bpy,json,hashlib,shutil
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_fitted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];keep={'Standing','Walking','Running','Attack'}
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
mat=bpy.data.materials.new('Guardian review clay');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.43,.43,.43,1);bs.inputs['Roughness'].default_value=.85;body.data.materials.clear();body.data.materials.append(mat)
for f in body.data.polygons:f.material_index=0
for o in bpy.data.objects:o.select_set(o in (rig,body))
bpy.context.view_layer.objects.active=rig;a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);out=P/'review/viewer';out.mkdir(parents=True,exist_ok=True);glb=out/'mm8_m592_pilot.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
sha=hashlib.sha256(glb.read_bytes()).hexdigest();provenance=json.loads((P/'motion_selection.json').read_text())['selected'];clips={a.name:{'label':a.name,'duration':(a.frame_range[1]-a.frame_range[0])/30,'mode':'once' if a.name=='Attack' else 'loop','provenance':provenance[a.name],'reference_note':'Native action evidence and adapted Ogre locomotion; not a frame trace.','anchors':[]} for a in bpy.data.actions};assert set(clips)==keep
manifest={'revision':'guardian_pilot_v1','model':glb.name,'default_model':'guardian_pilot','default_clip':'Attack','model_sha256':sha,'feedback':'feedback/user_feedback.json','models':[{'id':'guardian_pilot','label':'Plane Guardian — clay pilot','revision':'guardian_pilot_v1','url':glb.name+'?v='+sha[:12],'sha256':sha}],'clips':clips};(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
source=P.parent/'mm8_m540_claude/review/viewer';html=(source/'index.html').read_text().replace('Ogre Mage','Plane Guardian').replace('Mage','Guardian');(out/'index.html').write_text(html);shutil.copy2(source/'review.js',out/'review.js');print('EXPORTED',sha,flush=True)
