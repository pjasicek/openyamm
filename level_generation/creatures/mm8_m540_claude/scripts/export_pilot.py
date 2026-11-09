"""Export the four fitted pilot actions for the shared browser review."""
from pathlib import Path
import bpy,json,hashlib
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_fitted.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];wand=bpy.data.objects['Wand']
keep={'Standing','Walking','Running','Attack'}
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
mat=bpy.data.materials.new('Mage review clay');mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.43,.43,.43,1);bs.inputs['Roughness'].default_value=.85
for ob in [body,wand]:
 ob.data.materials.clear();ob.data.materials.append(mat)
 for face in ob.data.polygons:face.material_index=0
for ob in bpy.data.objects:ob.select_set(ob in (rig,body,wand))
bpy.context.view_layer.objects.active=rig
st=bpy.data.actions['Standing'];rig.animation_data.action=st
if st.slots:rig.animation_data.action_slot=st.slots[0]
bpy.context.scene.frame_set(0)
out=p/'review/viewer';out.mkdir(exist_ok=True,parents=True)
glb=out/'mm8_m540_pilot.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,
 export_anim_slide_to_zero=True)
sha=hashlib.sha256(glb.read_bytes()).hexdigest()
provenance={'Standing':'Local RelaxIdle with fitted Mage wand stance','Walking':'Completed MM6 Ogre Walking, fitted to Mage anatomy','Running':'Completed MM6 Ogre Running, fitted to Mage anatomy','Attack':'ArmedCastRAttack1 body with native waist charge and fitted wand release at 1.10 s'}
clips={a.name:{'label':a.name,'duration':(a.frame_range[1]-a.frame_range[0])/30,'mode':'once' if a.name=='Attack' else 'loop','provenance':provenance[a.name],'reference_note':'Adapted motion; exact native frame correspondence is not claimed.','anchors':[]} for a in bpy.data.actions}
assert set(clips)==keep
manifest={'revision':'mage_pilot_v1','model':glb.name,'default_model':'mage_pilot','default_clip':'Attack','model_sha256':sha,'feedback':'feedback/user_feedback.json','models':[{'id':'mage_pilot','label':'Ogre Mage — clay pilot','revision':'mage_pilot_v1','url':glb.name+'?v='+sha[:12],'sha256':sha}],'clips':clips}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PILOT_EXPORTED',sha,clips)
