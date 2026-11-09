from pathlib import Path
import bpy,sys,json
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
from club import add_club
club=add_club(rig)
g=json.loads((p/'work/grip_pose.json').read_text());c=Vector(g['handle_centre_hand_local']);a=Vector(g['handle_axis_hand_local'])
rot=Vector((0,0,1)).rotation_difference(a).to_matrix().to_4x4()
matrix=rig.data.bones['B_R_Hand'].matrix_local@Matrix.Translation(c)@rot
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('Club');b.parent=rig.data.edit_bones['B_R_Hand'];b.matrix=matrix;b.length=.1
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.selected_objects:o.select_set(False)
club.select_set(True);bpy.context.view_layer.objects.active=club
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
club.vertex_groups.new(name='Club').add(list(range(len(club.data.vertices))),1,'REPLACE')
club.modifiers.new('Rig','ARMATURE').object=rig
body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
keep={'Standing','Walking','Attack','Running','Hit','Death','Dead','Fidget'}
for act in list(bpy.data.actions):
 if act.name not in keep:bpy.data.actions.remove(act)
# Preserve the half-frame grounding keys in the exported animation.
for action in bpy.data.actions:
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:
      key.co.x*=2;key.handle_left.x*=2;key.handle_right.x*=2
 if action.use_frame_range:action.frame_start*=2;action.frame_end*=2
bpy.context.scene.render.fps=60
rig.animation_data.action=bpy.data.actions['Standing']
if len(rig.animation_data.action.slots):rig.animation_data.action_slot=rig.animation_data.action.slots[0]
for o in bpy.data.objects:o.select_set(o in (rig,body))
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_export.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'export/m440_full.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(p/'work/club_binding.json').write_text(json.dumps({'matrix': [list(r) for r in matrix],'grip_point':[0,0,0],'tip':[0,0,.75]},indent=2))

# Keep separate body/prop exports for actual-surface gate diagnostics.
import bmesh
bm=bmesh.new();bm.from_mesh(body.data);deform=bm.verts.layers.deform.active;idx=body.vertex_groups['Club'].index
verts=[v for v in bm.verts if v[deform].get(idx,0)>.999]
bmesh.ops.delete(bm,geom=verts,context='VERTS');bm.to_mesh(body.data);bm.free()
bpy.ops.export_scene.gltf(filepath=str(p/'export/m440_full_body.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True,export_all_influences=False,export_attributes=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
club=add_club(rig)
for v in club.data.vertices:v.co=rot.inverted().to_3x3()@(v.co-c)
club.matrix_world=Matrix();club.name='Club'
for o in bpy.data.objects:o.select_set(o==club)
bpy.context.view_layer.objects.active=club
bpy.ops.export_scene.gltf(filepath=str(p/'export/m440_full_club.glb'),use_selection=True,export_format='GLB',export_animations=False)
