"""A native straight silver dagger with brass hilt; the prop bone follows the hand except during the toss."""
import bpy, bmesh, sys, json, math
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_timed_twist.blend'))
rig=bpy.data.objects['Rig']; sc=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text()); C=Vector(G['handle_centre_hand_local']); A=Vector(G['handle_axis_hand_local']).normalized()
rig.animation_data.action=None
for b in rig.pose.bones: b.matrix_basis.identity()
H=rig.data.bones['B_R_Hand'].matrix_local; centre=H@C; axis=(H.to_3x3()@A).normalized()
flat=(H.to_3x3()@Vector((0,0,1))).normalized(); flat=(flat-axis*flat.dot(axis)).normalized()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('Dagger');b.head=centre;b.tail=centre+axis*.15;b.parent=rig.data.edit_bones['B_R_Hand'];b.align_roll(flat)
bpy.ops.object.mode_set(mode='OBJECT')
# Local blade axis +Y, flat faces +/-Z; slightly crowned steel with sharp edges and a pointed tip.
verts=[];faces=[];mi=[]
def ring(y,w,t):
    start=len(verts);verts.extend([(-w,y,0),(0,y,t),(w,y,0),(0,y,-t)]);return list(range(start,start+4))
rings=[ring(.060,.020,.003),ring(.265,.015,.002),ring(.325,.0001,.0001)]
for a,b in zip(rings[:-1],rings[1:]):
    for j in range(4):faces.append((a[j],a[(j+1)%4],b[(j+1)%4],b[j]));mi.append(0)
faces.append(tuple(reversed(rings[0])));mi.append(0)
# Hilt and grip are simple low-sided sections, with a narrow crossguard and rounded pommel.
def tube(y0,y1,rx,rz,mat):
    start=len(verts)
    for y in (y0,y1):
        for j in range(8):
            a=2*math.pi*j/8;verts.append((rx*math.cos(a),y,rz*math.sin(a)))
    faces.extend([tuple(start+j for j in reversed(range(8))),tuple(start+8+j for j in range(8))]);mi.extend([mat,mat])
    for j in range(8):faces.append((start+j,start+(j+1)%8,start+8+(j+1)%8,start+8+j));mi.append(mat)
tube(-.055,.045,.010,.010,1);tube(.045,.060,.045,.009,2);tube(-.067,-.055,.014,.012,2)
me=bpy.data.meshes.new('Dagger');me.from_pydata(verts,[],faces);me.update()
ob=bpy.data.objects.new('DaggerMesh',me);sc.collection.objects.link(ob)
for name,col,rough in [('Dagger_Steel',(.50,.54,.57,1),.32),('Dagger_Grip',(.20,.11,.045,1),.65),('Dagger_Brass',(.55,.35,.08,1),.40)]:
    m=bpy.data.materials.new(name);m.diffuse_color=col;m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=col;bs.inputs['Roughness'].default_value=rough
    me.materials.append(m)
for p,m in zip(me.polygons,mi):p.material_index=m
# Mesh in the rig's rest coordinates, rigid skin keeps the later split attachment reproducible.
me.transform(rig.data.bones['Dagger'].matrix_local)
ob.vertex_groups.new(name='Dagger').add(list(range(len(me.vertices))),1,'REPLACE')
ob.parent=rig;mod=ob.modifiers.new('Armature','ARMATURE');mod.object=rig
plan=json.loads((P/'work/fidget_plan.json').read_text()); release=plan['release_frame'];catch=plan['catch_frame'];mass=Vector((0,.12,0))
def act(a):
    rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def held(frame):
    sc.frame_set(int(frame),subframe=frame-int(frame));rig.pose.bones['Dagger'].matrix_basis.identity();bpy.context.view_layer.update()
    return (rig.matrix_world@rig.pose.bones['Dagger'].matrix).copy()
a=bpy.data.actions['Fidget'];act(a);M0=held(release);M1=held(catch)
P0=M0@mass;P1=M1@mass;T=(catch-release)/30; gravity=9.81
for a in [a for a in bpy.data.actions if a.use_fake_user]:
    act(a);prev=None
    # Half-frame keys retain the airborne catch exactly and keep the full spin below 180 degrees per key.
    frames=[i*.5 for i in range(int(a.frame_range[1]*2)+1)] if a.name=='Fidget' else list(range(int(a.frame_range[1])+1))
    for f in frames:
        sc.frame_set(int(f),subframe=f-int(f));b=rig.pose.bones['Dagger'];b.matrix_basis.identity();bpy.context.view_layer.update()
        if a.name=='Fidget' and release<f<catch:
            u=(f-release)/(catch-release);q=M0.to_quaternion().slerp(M1.to_quaternion(),u)
            q=Quaternion((0,1,0),2*math.pi*u)@q
            cm=P0.lerp(P1,u)+Vector((0,0,.5*gravity*T*T*u*(1-u)))
            m=q.to_matrix().to_4x4();m.translation=cm-q@mass;b.matrix=rig.matrix_world.inverted()@m
        b.rotation_mode='QUATERNION'
        if prev is not None and b.rotation_quaternion.dot(prev)<0:b.rotation_quaternion=-b.rotation_quaternion
        prev=b.rotation_quaternion.copy();b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
act(None)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_props.blend'))
print('DAGGER',sum(len(p.vertices)-2 for p in me.polygons),'triangles; toss',release,catch)
