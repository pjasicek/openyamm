from pathlib import Path
import sys,bpy,numpy as np,bmesh
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
for part,color in [(2,(.25,.7,.3,1)),(16,(1,.25,.02,1)),(33,(1,.25,.02,1)),(10,(.1,.3,1,1))]:
 m=bpy.data.materials.new(str(part));m.diffuse_color=color;me.materials.append(m)
 for f in me.polygons:
  if pv[f.vertices[0]]==part:f.material_index=len(me.materials)-1
common.workbench_clay(scene)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
for part in (10,16):
 c=np.array([tuple(v.co) for v in me.vertices if pv[v.index]==part]);print('PART REST',part,c.min(0),c.max(0))
common.render_views(str(p/'review/skirt_rest'),.90,.75,views=('front','left','back'),resolution=(720,720))

for name,f in [('Attack',20),('Walking',19),('Running',1)]:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(f)
 c=rig.pose.bones['B_Pelvis'].head
 common.render_views(str(p/f'review/skirt_{name}'),c.z-.12,.95,views=('front','left','right','three_quarter','back'),target=(c.x,c.y),resolution=(720,720))
