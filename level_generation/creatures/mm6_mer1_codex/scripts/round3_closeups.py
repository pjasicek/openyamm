import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
for label,path in [('before','work/round3/before.glb'),('after','export/mm6_mer1_portable_a.glb')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/path));s=bpy.context.scene;r=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 for o in list(bpy.data.objects):
  if o.type=='MESH'and not any(m.type=='ARMATURE'for m in o.modifiers):bpy.data.objects.remove(o,do_unlink=True)
 s.render.engine='BLENDER_EEVEE';s.world=bpy.data.worlds.new('Closeup world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;s.render.film_transparent=True
 if hasattr(s,'eevee'):s.eevee.taa_render_samples=32
 for pos,power in [((4,-4,5),500),((-3,-1,3),300),((0,3,4),400)]:
  data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.shape='DISK';data.size=5;o=bpy.data.objects.new('Softbox',data);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]=='Standing');r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(0)
 common.render_views(str(P/'review/round3'/f'{label}_face'),1.52,.43,views=('front','left','three_quarter'),resolution=(800,800))
 # Isolate the left hand for palm/back views: the relaxed palm faces the thigh and is otherwise occluded.
 source=next(o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE'for m in o.modifiers));keep={v.index for v in source.data.vertices if sum(g.weight for g in v.groups if source.vertex_groups[g.group].name.startswith(('B_L_Hand','B_L_Finger')))>.3};ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(ev);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in keep],context='VERTS');bm.to_mesh(me);bm.free();hand=bpy.data.objects.new('Isolated exported left hand',me);s.collection.objects.link(hand);hand.matrix_world=source.matrix_world.copy();source.hide_render=True
 palms=json.loads((P/'work/round2/palm_normals.json').read_text());h=r.pose.bones['B_L_Hand'];finger=r.pose.bones['B_L_Finger22'];center=sum((hand.matrix_world@v.co for v in hand.data.vertices),Vector())/len(hand.data.vertices);normal=(r.matrix_world.to_3x3()@h.matrix.to_3x3()@Vector(palms['L'])).normalized()
 for name,sign in [('palm',1),('back',-1)]:
  loc=center+normal*sign;cam=common.ortho_camera('Hand closeup',tuple(loc),tuple((center-loc).to_track_quat('-Z','Y').to_euler()),.235);s.camera=cam;s.render.resolution_x=s.render.resolution_y=800;s.render.filepath=str(P/'review/round3'/f'{label}_hand_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
