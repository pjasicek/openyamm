"""Transfer the rebaked master's atlas and normal field without moving geometry or skin weights."""
import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import pbr_round3 as pbr
selection=json.loads((R/'lod_selection.json').read_text())
def transfer(lod):
 row=next(r for r in selection if r['lod']==lod);bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 initial=set(bpy.data.objects);initial_actions=set(bpy.data.actions)
 with bpy.data.libraries.load(str(W/'rebaked_l0.blend'),link=False)as(src,dst):dst.objects=['Body']
 master=dst.objects[0];bpy.context.scene.collection.objects.link(master);master.parent=None;master.matrix_world=body.matrix_world.copy()
 for md in master.modifiers:md.show_viewport=False;md.show_render=False
 before=np.array([v.co[:]for v in body.data.vertices]);weights=[[(g.group,g.weight)for g in v.groups]for v in body.data.vertices]
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
 md=body.modifiers.new('Shared rebaked atlas','DATA_TRANSFER');md.object=master;md.use_loop_data=True;md.data_types_loops={'CUSTOM_NORMAL'};md.loop_mapping='POLYINTERP_NEAREST';md.layers_uv_select_src='ALL';md.layers_uv_select_dst='NAME';md.islands_precision=.1
 bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 assert np.array_equal(before,np.array([v.co[:]for v in body.data.vertices]));assert weights==[[(g.group,g.weight)for g in v.groups]for v in body.data.vertices]
 for o in set(bpy.data.objects)-initial:bpy.data.objects.remove(o,do_unlink=True)
 for a in set(bpy.data.actions)-initial_actions:bpy.data.actions.remove(a)
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.wm.save_as_mainfile(filepath=str(W/f'rebaked_l{lod}.blend'));bpy.ops.export_scene.gltf(filepath=str(W/f'geometry_body_l{lod}.glb'),use_selection=True,export_format='GLB',export_animations=False,export_all_influences=True,export_attributes=False)
if __name__=='__main__':
 transfer(1);pbr.render('low','a','normal_transfer_l1',550,1,views=[0,1])
