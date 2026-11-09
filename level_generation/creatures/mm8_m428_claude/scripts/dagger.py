"""The Dagger bone at the solved grip (same construction as mm8_m424_claude/scripts/dagger.py, so the installed male
dagger attachment mm8_m424_dagger.glb, authored in that bone's space, fits this hand unchanged) and a review copy of
the dagger mesh (rigid on Dagger; not exported in the body GLB)."""
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
# The dagger never leaves the hand (no toss in this fidget): the Dagger bone keeps its rest pose in every clip.
for a in [a for a in bpy.data.actions if a.use_fake_user]:
    rig.animation_data.action=a
    if len(a.slots):rig.animation_data.action_slot=a.slots[0]
    b=rig.pose.bones['Dagger'];b.rotation_mode='QUATERNION';b.matrix_basis.identity()
    for f in (int(a.frame_range[0]),int(a.frame_range[1])):
        b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_props.blend'))
print('DAGGER',sum(len(p.vertices)-2 for p in me.polygons),'triangles')
