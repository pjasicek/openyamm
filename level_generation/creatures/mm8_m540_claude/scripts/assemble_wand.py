"""Fit the generated wand's grip to the measured palm and retain it as a rigid bone attachment."""
from pathlib import Path
import bpy,sys,json,math,numpy as np
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_sources.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/wand_v1/model_urls_glb.glb'))
new=set(bpy.data.objects)-before;meshes=[o for o in new if o.type=='MESH']
for o in bpy.context.view_layer.objects:o.select_set(o in meshes)
bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join()
wand=bpy.context.object;wand.name='Wand';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in wand.data.vertices]);lo,hi=co.min(0),co.max(0);height=hi[2]-lo[2]
edges=np.array([tuple(e.vertices) for e in wand.data.edges])
def section(z):
 a,b=co[edges[:,0]],co[edges[:,1]]
 hit=(a[:,2]-z)*(b[:,2]-z)<0
 a,b=a[hit],b[hit]
 assert len(a)>3,(z,lo.tolist(),hi.tolist())
 return a+(b-a)*((z-a[:,2])/(b[:,2]-a[:,2]))[:,None]
rings=[section(lo[2]+t*height) for t in [.10,.23]]
centres=[(ring.min(0)+ring.max(0))/2 for ring in rings]
centre=centres[0];axis=centres[1]-centres[0];axis/=np.linalg.norm(axis)
R=Vector(axis).rotation_difference(Vector((0,0,1))).to_matrix()
co=(np.array(R)@(co-centre).T).T
co*=.50/np.ptp(co[:,2]);zmin=co[:,2].min();grip_z=zmin+.20*.50
band=section(grip_z)
xy=(band[:,:2].min(0)+band[:,:2].max(0))/2
co[:,:2]-=xy;co[:,2]-=grip_z
g=json.loads((p/'work/grip_pose.json').read_text());radius=g['radius']
raw_radius=max(float(np.linalg.norm(section(z)[:,:2],axis=1).max()) for z in [-.035,0,.035])
assert .01<raw_radius<.065,raw_radius
factor=radius/raw_radius
for v in co:
 blend=np.clip((.14-v[2])/.06,0,1)
 v[:2]*=1+(factor-1)*blend
orb_zone=co[co[:,2]>.28];orb=Vector(((orb_zone[:,0].min()+orb_zone[:,0].max())/2,(orb_zone[:,1].min()+orb_zone[:,1].max())/2,(orb_zone[:,2].min()+orb_zone[:,2].max())/2))
H=rig.data.bones['B_R_Hand'].matrix_local
local=Vector((0,0,1)).rotation_difference(Vector(g['handle_axis_hand_local'])).to_matrix().to_4x4()
roll=json.loads((p/'work/wand_orientation.json').read_text())['roll_radians']
local=local@Matrix.Rotation(roll,4,'Z')
local.translation=Vector(g['handle_centre_hand_local']);M=H@local
for v,c in zip(wand.data.vertices,co):v.co=M@Vector(c)
for f in wand.data.polygons:f.use_smooth=True
for o in bpy.context.view_layer.objects:o.select_set(o is rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,loc,parent in [('Wand',M.translation,'B_R_Hand'),('Socket_WandOrb',M@orb,'Wand')]:
 eb=rig.data.edit_bones.new(name);eb.head=loc;eb.tail=loc+M.to_3x3().col[1]*.04
 eb.align_roll(M.to_3x3().col[2]);eb.parent=rig.data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
wand.vertex_groups.clear();vg=wand.vertex_groups.new(name='Wand');vg.add(list(range(len(wand.data.vertices))),1,'REPLACE')
wand.parent=rig;mod=wand.modifiers.new('Armature','ARMATURE');mod.object=rig
for o in new:
 if o.name in bpy.data.objects and o is not wand and o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
for act in [bpy.data.actions[n] for n in ['Standing','Walking','Running','CastSource']]:
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 for n,q in g['finger_local'].items():
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q
  for f in (int(act.frame_range[0]),int(act.frame_range[1])):pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_wand.blend'))
report={'height_m':.50,'grip_radius_m':radius,'grip_radius_before_fit':float(raw_radius),'shaft_radius_factor':float(factor),'orb_wand_local':list(orb),'attachment_bone':'Wand','release_socket':'Socket_WandOrb','triangles':sum(len(f.vertices)-2 for f in wand.data.polygons)}
(p/'review/geometry/wand_fit.json').write_text(json.dumps(report,indent=2)+'\n');print('WAND_FIT',report)
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(0)
print('READY_JOINTS',{n:list(rig.pose.bones[n].head) for n in ['B_R_Hand','B_L_Hand','B_R_Forearm','B_L_Forearm']},flush=True)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/pilot_unmodified'),.9,2.2,views=('front','left','back','three_quarter'),resolution=(600,700))
