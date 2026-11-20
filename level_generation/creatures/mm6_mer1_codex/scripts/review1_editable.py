import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];d=json.loads((P/'review/reduction/selection.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction/selected_lod0.blend'))
o=bpy.data.objects['Body'];bs=o.data.materials[0].node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].links[0].from_node.image=bpy.data.images.load(str(P/d['body'][0]['textures']/'mer1_a_preview.png'),check_existing=False)
r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0);report=json.loads(bpy.context.scene.get('retarget_report','{}'));report['Running']={'source':'mixamo','clip':'anim_library/mixamo/Jogging.fbx','fitted_duration_s':.8,'stride_m':1.302};bpy.context.scene['retarget_report']=json.dumps(report);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_mer1.blend'))
