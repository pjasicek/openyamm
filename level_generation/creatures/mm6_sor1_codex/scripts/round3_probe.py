import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/production_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff']
g=json.loads((p/'work/grip_pose.json').read_text());H=rig.data.bones['B_R_Hand'].matrix_local;C=H@Vector(g['handle_centre_hand_local']);A=(H.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized();along=[(v.co-C).dot(A) for v in staff.data.vertices]
print('STAFF',list(C),list(A),min(along),max(along),[(n,rig.data.bones[n].parent.name if rig.data.bones[n].parent else None) for n in ['B_Staff','Socket_Staff_Head']])
print('MATERIALS',[(m.name,[(n.type,n.image.name if n.type=='TEX_IMAGE' and n.image else '') for n in m.node_tree.nodes]) for m in body.data.materials]);print('PARTS',[(i,sum(len(f.vertices)-2 for f in body.data.polygons if body.data.attributes['piece'].data[f.vertices[0]].value==i)) for i in sorted(set(a.value for a in body.data.attributes['piece'].data))])
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(p.parents[2]/'anim_library/humanoid_set/2Hand Spear.glb'));arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=next(a for a in bpy.data.actions if a.name.endswith('2HandSpearAttack1'));arm.animation_data.action=act;arm.animation_data.action_slot=act.slots[0];W=Matrix.Rotation(math.pi,4,'Z')@arm.matrix_world
rows=[]
for f in range(37):
 scene.frame_set(f+int(act.frame_range[0]));rows.append({n:[list(row) for row in W@pb.matrix] for n,pb in arm.pose.bones.items()})
(p/'work/source_spear_r3.json').write_text(json.dumps({'fps':30,'duration':1.2,'poses':rows,'rest':{b.name:[list(row) for row in W@b.matrix_local] for b in arm.data.bones}}))
