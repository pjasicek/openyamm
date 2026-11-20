"""Fit separately animated equipment to the fitted source-frame rig."""
from pathlib import Path
import bpy,sys,json,math,numpy as np
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
source=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else str(P/'work/texture_master.blend')
bpy.ops.wm.open_mainfile(filepath=source);r=bpy.data.objects['Rig'];sc=bpy.context.scene;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();cfg=json.loads((P/'work/props.json').read_text());rel=Matrix(cfg['crossbow_hand_matrix']);CB=r.data.bones['B_R_Hand'].matrix_local@rel.inverted()
def line(tip,nock):
 tip,nock=Vector(tip),Vector(nock);d=nock-tip;M=d.to_track_quat('Y','Z').to_matrix().to_4x4();M.translation=tip;return M,d.length
Q=Matrix.Rotation(math.radians(cfg['quiver_rest_rotation_y_degrees']),4,'Y')@Matrix.Rotation(math.radians(-90),4,'Z');Q.translation=Vector(cfg['quiver_rest_position'])
rest={'Crossbow':CB,'Bolt':CB,'Quiver':Q};parents={'Crossbow':'B_R_Hand','Bolt':'Crossbow','Quiver':'B_Pelvis'}
for i,s in enumerate('LR'):rest['String'+s]=CB@line(cfg['string_tips'][i],cfg['nock_drawn'])[0];parents['String'+s]='Crossbow'
S=CB.copy();S.translation=CB@Vector((0,.41,.09));rest['Socket_Bolt']=S;parents['Socket_Bolt']='Crossbow'
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for n,M in rest.items():
 b=r.data.edit_bones.new(n);b.length=.08;b.matrix=M;b.parent=r.data.edit_bones[parents[n]];b.use_deform=n!='Socket_Bolt'
bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(P/'work/props.blend'),link=False) as (src,dst):dst.objects=['CrossbowMesh','BoltMesh','QuiverMesh','StringMesh']
props={}
for o in dst.objects:
 sc.collection.objects.link(o);props[o.name]=o
right=props['StringMesh'].copy();right.data=props['StringMesh'].data.copy();sc.collection.objects.link(right);right.name='StringRMesh';props[right.name]=right;props['StringMesh'].name='StringLMesh'
for o in props.values():
 n=o.name.removesuffix('Mesh');o.data.transform(rest[n]);o.matrix_world=Matrix();o.vertex_groups.new(name=n).add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=r;mod=o.modifiers.new('Rig','ARMATURE');mod.object=r
for a in list(bpy.data.actions):
 if not a.use_fake_user or a.name=='Dead':continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1])
 for f in range(end+1):
  sc.frame_set(f);t=f/30;release=a.name=='Attack' and 1<=t<1.56
  amount=min(1,max(0,(t-1)*30)) if release else 0
  nock=Vector(cfg['nock_drawn']).lerp(Vector(cfg['nock_released']),amount)
  for i,s in enumerate('LR'):
   pb=r.pose.bones['String'+s];M,L=line(cfg['string_tips'][i],nock);M=M@Matrix.Diagonal((L,L,L,1));pb.matrix=r.pose.bones['Crossbow'].matrix@M;pb.rotation_mode='QUATERNION'
   for path in ['rotation_quaternion','location','scale']:pb.keyframe_insert(path,frame=f)
  pb=r.pose.bones['Bolt'];pb.scale=(.000001,)*3 if release and t>1.001 else (1,)*3;pb.keyframe_insert('scale',frame=f)
 for la in a.layers:
  for st in la.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
for o in bpy.data.objects:
 if o.type=='MESH' and o not in [bpy.data.objects['Body'],*props.values()]:o.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipped_source.blend'))
common.workbench_clay(sc,textured=True)
for role,times in [('Standing',[0]),('Attack',[.33,.70,1,1.06,1.4]),('Running',[.2]),('Death',[.2,.8,1.533]),('Fidget',[.4,.8])]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for t in times:
  sc.frame_set(round(t*30));common.render_views(str(P/f'review/equipped_{role}_{t:.2f}'),.9,2.3,views=('front','left'),resolution=(520,700))
print('EQUIPPED',list(rest))
