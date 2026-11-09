from pathlib import Path
import bpy,sys,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene)
# A visible stand-in tests the full blade sweep before the final native sword is modelled.
import bmesh
from mathutils import Vector
G=json.loads((p/'work/grip_pose.json').read_text());c=Vector(G['handle_centre_hand_local']);ax=Vector(G['handle_axis_hand_local']);side=ax.orthogonal().normalized();flat=ax.cross(side)
bm=bmesh.new()
for a0,a1,w,d in [(-.06,.06,.012,.012),(.06,.08,.08,.012),(.08,.68,.027,.003)]:
 vs=[bm.verts.new(c+ax*a+side*x*w+flat*y*d) for a in [a0,a1] for x in [-1,1] for y in [-1,1]]
 for q in [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]:bm.faces.new([vs[j] for j in q])
mesh=bpy.data.meshes.new('sword');bm.to_mesh(mesh);bm.free();sword=bpy.data.objects.new('sword',mesh);scene.collection.objects.link(sword)
rows=[]
for name in ['Standing','Walking','Running','Attack','Hit','Cast','Death','Fidget']:
 act=bpy.data.actions[name];rig.animation_data.action=act
 if len(act.slots):rig.animation_data.action_slot=act.slots[0]
 row=[]
 for i in range(6):
  f=act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/5;scene.frame_set(int(f),subframe=f-int(f))
  sword.matrix_world=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix
  paths=common.render_views(str(p/'review/motion_pilot'/f'{name}_{i}'),.85,2.1,views=('front','right'),resolution=(220,340));row.append([paths[0],f'{name} {f/30:.2f}s'])
 rows.append(row)
(p/'review/motion_pilot/frames.json').write_text(json.dumps(rows))
