import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v6.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text());HM=rig.data.bones['B_L_Hand'].matrix_local;C=Vector(G['handle_centre_hand_local']);A=Vector(G['handle_axis_hand_local'])
def action(n):
 a=bpy.data.actions[n];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];return a
at=action('Attack');dist=[]
for f in range(int(at.frame_range[1])+1):
 scene.frame_set(f);hp=rig.pose.bones['B_L_Hand'].matrix;centre=hp@C;rp=rig.pose.bones['B_R_Hand'].head;dist.append((f,(rp-centre).length,list(rp),list(centre)))
fr=12;scene.frame_set(fr)
hp=rig.pose.bones['B_L_Hand'].matrix;ax=(hp.to_3x3()@A).normalized();behind=rig.pose.bones['B_R_Hand'].head-(hp@C);behind=(behind-ax*behind.dot(ax)).normalized();bx=behind.cross(ax).normalized();rot=Matrix([bx,behind,ax]).transposed();local=hp.to_3x3().inverted()@rot
(P/'work/bow_pose.json').write_text(json.dumps({'draw_max_frame':fr,'draw_trace':dist,'bow_rotation_hand_local':[list(r)for r in local],'bow_origin_hand_local':list(C)},indent=2))
with bpy.data.libraries.load(str(P/'work/bow_textured.blend'),link=False)as(src,dst):dst.objects=['BowArrow']
bow=dst.objects[0];scene.collection.objects.link(bow)
# Review excludes the loose design arrow; the action gets a separate nocked arrow later.
import bmesh
bm=bmesh.new();bm.from_mesh(bow.data);pa=bm.faces.layers.int.get('prop_part');bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[pa]>=5],context='FACES');bm.to_mesh(bow.data);bm.free()
rest=HM@Matrix.Translation(C)@local.to_4x4();bow.matrix_world=rest
common.workbench_clay(scene,textured=True);rows=[]
for n in ['Standing','Walking','Running','Attack','Hit','Death']:
 a=action(n);row=[]
 for i,f in enumerate(np.linspace(*a.frame_range,5)):
  scene.frame_set(int(f),subframe=float(f-int(f)));hp=rig.pose.bones['B_L_Hand'].matrix;bow.matrix_world=hp@Matrix.Translation(C)@local.to_4x4()
  out=common.render_views(str(P/f'review/poses/{n}_{i}'),.85,2.25,views=('front','left','three_quarter'),resolution=(360,450))
  row.append({'frame':float(f),'paths':out})
 rows.append({'action':n,'frames':row})
(P/'review/poses/index.json').write_text(json.dumps(rows,indent=2));print('DRAWTRACE',dist)
