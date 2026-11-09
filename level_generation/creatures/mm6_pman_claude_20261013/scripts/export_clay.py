from pathlib import Path
import bpy,json,sys,runpy,hashlib
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/repair_face.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/texture_ready.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
mat=bpy.data.materials.new('PeasantClay');mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.45,.45,.45,1);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.85
me.materials.clear();me.materials.append(mat)
for f in me.polygons:f.material_index=0
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0)
out=p/'review/viewer/pman_clay.glb'
bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
clips={a.name:{'label':a.name,'duration':float(a.frame_range[1])/30,'mode':'loop' if a.name in ('Standing','Walking') else 'once','provenance':'Retargeted local library motion; civilian fitting','anchors':[]} for a in bpy.data.actions}
assert set(clips)=={'Standing','Walking','Hit','Fidget','Death','Dead'}
sha=hashlib.sha256(out.read_bytes()).hexdigest();model={'id':'clay','label':'New peasant — clay review','revision':'pman_clay_v1','url':out.name+'?v=1','sha256':sha}
(p/'review/viewer/manifest.json').write_text(json.dumps({'revision':'pman_clay_v1','model':model['url'],'model_sha256':sha,'default_model':'clay','default_clip':'Standing','models':[model],'clips':clips,'feedback':'feedback/user_feedback.json'},indent=2))
