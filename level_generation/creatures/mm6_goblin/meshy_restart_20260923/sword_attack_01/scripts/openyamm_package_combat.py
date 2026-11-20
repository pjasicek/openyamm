import bpy,json,traceback,math
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];body=s.objects['Goblin_Combat_Body'];keys=['Idle','Walk','Run','Attack','GripRest'];acts=[bpy.data.actions['MM6_Goblin_'+k] for k in keys]
# Preserve every authored half-frame at export using a 48-fps timeline with unchanged seconds.
if not s.get('combat_delivery_48fps'):
 for a in acts:
  start=a.frame_range[0]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for kp in fc.keyframe_points:
       kp.co.x=1+(kp.co.x-start)*2;kp.handle_left.x=1+(kp.handle_left.x-start)*2;kp.handle_right.x=1+(kp.handle_right.x-start)*2
 s['combat_delivery_48fps']=True
s.render.fps=48
for tr in list(r.animation_data.nla_tracks):r.animation_data.nla_tracks.remove(tr)
for a in acts:
 tr=r.animation_data.nla_tracks.new();tr.name=a.name;st=tr.strips.new(a.name,1,a);st.action_slot=a.slots[0];tr.mute=True
# Use portable constant materials for this weapon; no unsupported procedural texture dependency.
mat=bpy.data.materials['Corsair - dark leather']
for node in list(mat.node_tree.nodes):
 if node.type not in ['BSDF_PRINCIPLED','OUTPUT_MATERIAL']:mat.node_tree.nodes.remove(node)
# Tiny helper bones are not useful in a normal viewport.
for pb in r.pose.bones:pb.custom_shape=None
r.show_in_front=False
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  sp=area.spaces.active;sp.shading.type='MATERIAL';sp.overlay.show_overlays=False;sp.region_3d.view_location=(0,0,.95);sp.region_3d.view_distance=3;sp.region_3d.view_rotation=Vector((0,-4,0)).to_track_quat('Z','Y');sp.region_3d.view_perspective='ORTHO'
a=bpy.data.actions['MM6_Goblin_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_start=1;s.frame_end=37;s.frame_set(7);s.camera.location=(0,-5,.98);s.camera.rotation_euler=(Vector((0,0,.98))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=2.65
bpy.ops.object.select_all(action='DESELECT')
for o in s.objects:
 if o.type in ['MESH','ARMATURE']:o.select_set(True)
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(OUT/'mm6_goblin_corsair_attack.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=False,export_force_sampling=True,export_tangents=True)
bpy.data.libraries.write(str(OUT/'mm6_goblin_corsair_attack.blend'),{s},fake_user=True,compress=True)
report={'body_triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'weapon_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in s.objects if o.type=='MESH' and o.get('goblin_weapon')),'bones':len(r.data.bones),'clips':[{'name':a.name,'frame_range':list(a.frame_range),'seconds':(a.frame_range[1]-a.frame_range[0])/48} for a in acts],'fps':48,'maximum_body_vertex_influences':max(len(v.groups) for v in body.data.vertices),'maximum_weight_sum_error':max(abs(sum(g.weight for g in v.groups)-1) for v in body.data.vertices)}
# Reusable standalone sword: grip-center origin, +Y blade, +Z blade curvature, +X thickness.
w=bpy.data.scenes.new('Corsair - Standalone Sword');bpy.context.window.scene=w;S=Matrix(json.loads((OUT/'sword_build.json').read_text())['sword_rest_transform']);new=[]
for ob in s.objects:
 if ob.type=='MESH' and ob.get('goblin_weapon'):
  cp=ob.copy();cp.data=ob.data.copy();w.collection.objects.link(cp);cp.parent=None;cp.matrix_world=Matrix.Identity(4);cp.modifiers.clear();cp.vertex_groups.clear()
  for v in cp.data.vertices:v.co=S.inverted()@v.co
  new.append(cp)
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.context.view_layer.objects.active=new[0];bpy.ops.object.join();new[0].name='Corsair Goblin Sword';bpy.ops.export_scene.gltf(filepath=str(OUT/'corsair_goblin_sword.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False)
bpy.context.window.scene=s;(OUT/'delivery_manifest.json').write_text(json.dumps(report,indent=2));(OUT/'package_done.txt').write_text('complete');print(json.dumps(report))
