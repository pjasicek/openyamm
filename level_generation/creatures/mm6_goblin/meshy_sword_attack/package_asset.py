"""Export the isolated working scene and the reusable weapon; retain imported clips as named references."""
import bpy,json
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack')
s=bpy.data.scenes['Meshy Goblin Sword and Native Attack'];bpy.context.window.scene=s;r=bpy.data.objects['MM6 Meshy Goblin Rig'];source=json.loads(s['source_actions']);authored=json.loads(s['authored_actions'])
r.animation_data.action=None
for t in list(r.animation_data.nla_tracks):r.animation_data.nla_tracks.remove(t)
tracks=[('MM6_Standing_Sword',authored['Standing']),('MM6_Attack_Native',authored['Attack'])]
tracks.extend(('Meshy_'+label,name) for label,name in source.items())
for label,name in tracks:
 a=bpy.data.actions[name];tr=r.animation_data.nla_tracks.new();tr.name=label;strip=tr.strips.new(label,int(a.frame_range[0]),a);strip.action_slot=a.slots[0];strip.extrapolation='NOTHING';strip.blend_type='REPLACE'
for o in bpy.context.view_layer.objects:o.select_set(False)
r.select_set(True)
for o in s.objects:
 if o.type=='MESH' and o.find_armature()==r:o.select_set(True)
bpy.context.view_layer.objects.active=r;s.frame_set(0)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'goblin_sword_attack.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_skins=True,export_anim_slide_to_zero=True,export_optimize_animation_size=False,export_current_frame=False)
for tr in r.animation_data.nla_tracks:tr.mute=True
a=bpy.data.actions[authored['Standing']];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(1)
# Save only this scene's dependency graph, not the user's other open review scenes.
for o in s.objects:
 if o.type=='MESH':
  for m in o.data.materials:
   if m and m.use_nodes:
    for n in m.node_tree.nodes:
     if n.type=='TEX_IMAGE' and n.image and not n.image.packed_file:n.image.pack()
s.camera.data.ortho_scale=2.4;s.camera.location=(-3,-5,1.1);s.camera.rotation_euler=(Vector((0,0,1.0))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.render.film_transparent=True
bpy.data.libraries.write('/tmp/openyamm_goblin_sword_scene.blend',{s},fake_user=True)
# A separate static sword, centered on its grip and oriented along Blender +Y.
weapon_scene=bpy.data.scenes.new('Standalone MM6 goblin sword');bpy.context.window.scene=weapon_scene
hand=r.data.bones['mixamorig:RightHand'].matrix_local;grip=Vector(s['sword_grip_local']);rot=Matrix(json.loads(s['sword_in_hand']));inv=(hand@Matrix.Translation(grip)@rot.to_4x4()).inverted()
for original in s.objects:
 if not original.get('mm6_sword_part'):continue
 o=original.copy();o.data=original.data.copy();weapon_scene.collection.objects.link(o);o.parent=None;o.matrix_world=Matrix.Identity(4)
 for mod in list(o.modifiers):o.modifiers.remove(mod)
 for group in list(o.vertex_groups):o.vertex_groups.remove(group)
 for v in o.data.vertices:v.co=inv@v.co
 o.select_set(True)
bpy.context.view_layer.objects.active=next(iter(weapon_scene.objects));bpy.ops.object.join();sword=bpy.context.object;sword.name='MM6 Goblin Curved Sword'
bpy.ops.export_scene.gltf(filepath=str(ROOT/'mm6_goblin_sword.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_skins=False)
bpy.context.window.scene=s
print('Exported animated goblin, standalone sword, and isolated scene library for project save')
