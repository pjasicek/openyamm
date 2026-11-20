from pathlib import Path
import bpy,bmesh,sys,json
import numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_grip.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0)
g=json.loads((p/'work/grip_pose.json').read_text());H=rig.pose.bones['B_R_Hand'].matrix;C=H@Vector(g['handle_centre_hand_local'])
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());bm=bmesh.new();bm.from_mesh(ev.to_mesh());ev.to_mesh_clear()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.co-C).length>.23],context='VERTS')
lab=bm.verts.layers.int['finger']
for f in bm.faces:f.material_index=max(set(v[lab] for v in f.verts),key=lambda x:sum(v[lab]==x for v in f.verts))
me=bpy.data.meshes.new('HandDebug');bm.to_mesh(me);bm.free();ob=bpy.data.objects.new('HandDebug',me);bpy.context.collection.objects.link(ob);body.hide_render=True
for i,col in enumerate([(0.5,.5,.5,1),(1,.1,.1,1),(.1,1,.1,1),(.1,.1,1,1),(1,0,1,1),(1,1,.1,1)]):
 m=bpy.data.materials.new(str(i));m.diffuse_color=col;me.materials.append(m)
for n in ['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']:
 print('THUMBPOSE',n,list(rig.pose.bones[n].head),list(rig.pose.bones[n].rotation_quaternion))
common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='MATERIAL'
common.render_views(str(p/'review/grip_weights'),C.z,.42,views=('front','left','three_quarter'),resolution=(700,700),target=(C.x,C.y))
