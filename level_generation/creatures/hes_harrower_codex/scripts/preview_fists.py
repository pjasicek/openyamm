"""Inspect actual posed hand skin around the solved handle; background Blender images only."""
from pathlib import Path
import bpy,bmesh,json,numpy as np
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];out=P/'review/r2';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/review_v1/final.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for side in 'LR':
 g=json.loads((P/f'work/grip_pose_r2_{side}.json').read_text())
 for n,q in g['finger_local'].items():rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=Quaternion(q)
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dep);posed=ev.to_mesh();names=[g.name for g in body.vertex_groups];report={}
for o in bpy.data.objects:o.hide_render=True
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.render.film_transparent=True
scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100
for side in 'LR':
 g=json.loads((P/f'work/grip_pose_r2_{side}.json').read_text());H=rig.data.bones[f'B_{side}_Hand'].matrix_local;C=H@Vector(g['handle_centre_hand_local']);A=(H.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized();F=H.to_3x3()@Vector((0,1,0));N=A.cross(F).normalized()
 if side=='L':N=-N
 mask=[sum(vg.weight for vg in v.groups if names[vg.group].startswith(f'B_{side}_Finger') or names[vg.group]==f'B_{side}_Hand')>.5 for v in body.data.vertices]
 bm=bmesh.new();bm.from_mesh(posed);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if not mask[v.index]],context='VERTS');mesh=bpy.data.meshes.new('posed_hand_'+side);bm.to_mesh(mesh);bm.free();ob=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(ob)
 for i,m in enumerate(mesh.materials):
  if m:m=m.copy();m.diffuse_color=(.58,.49,.38,1) if 'Claws' in m.name else (.32,.055,.13,1);mesh.materials[i]=m
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=g['radius'],depth=.18,location=C);cyl=bpy.context.object;cyl.rotation_mode='QUATERNION';cyl.rotation_quaternion=A.to_track_quat('Z','Y');mat=bpy.data.materials.new('handle_'+side);mat.diffuse_color=(.8,.45,.08,1);cyl.data.materials.append(mat)
 coords=np.array([list(H.inverted()@v.co) for v in posed.vertices]);c=np.array(g['handle_centre_hand_local']);a=np.array(g['handle_axis_hand_local']);q=coords-c;rad=np.linalg.norm(q-np.outer(q@a,a),axis=1);along=q@a
 stats={}
 for finger in range(5):
  prefix=f'B_{side}_Finger{finger}';use=np.array([sum(vg.weight for vg in v.groups if names[vg.group].startswith(prefix))>.5 for v in body.data.vertices])&(np.abs(along)<.09)
  stats[str(finger)]={'min_gap_m':float(rad[use].min()-g['radius']),'p10_gap_m':float(np.percentile(rad[use],10)-g['radius'])} if use.any() else None
 report[side]=stats;print('HAND_SKIN',side,stats,flush=True)
 for name,direction in [('palm',N),('axis',A),('fingers',F),('quarter',(N+F).normalized())]:
  cd=bpy.data.cameras.new('review');cam=bpy.data.objects.new('review',cd);scene.collection.objects.link(cam);cam.location=C+direction;cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=.38;scene.camera=cam;scene.render.filepath=str(out/f'grip_{side}_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 ob.hide_render=True;cyl.hide_render=True
(P/'review/r2/grip_skin.json').write_text(json.dumps(report,indent=2)+'\n');ev.to_mesh_clear()
