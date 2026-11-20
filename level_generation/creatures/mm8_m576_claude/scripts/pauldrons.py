"""Shoulder armour follows the clavicle, lifting outward for overhead reach without inheriting arm roll."""
import bpy,sys,math
from mathutils import Vector,Matrix,Quaternion
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import armik
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for side in 'LR':
    name=f'Pauldron_{side}';b=rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name)
    b.head=rig.data.edit_bones[f'B_{side}_UpperArm'].head;b.tail=b.head+Vector((0,0,.1));b.parent=rig.data.edit_bones[f'B_{side}_Clavicle']
bpy.ops.object.mode_set(mode='OBJECT')
for act in bpy.data.actions:
    rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
    for f in range(int(act.frame_range[1])+1):
        bpy.context.scene.frame_set(f)
        for side,sgn in [('L',1),('R',-1)]:
            C=armik.W(rig,f'B_{side}_Clavicle');Cr=rig.data.bones[f'B_{side}_Clavicle'].matrix_local
            D=C@Cr.inverted();a=armik.W(rig,f'B_{side}_Forearm').translation-armik.W(rig,f'B_{side}_UpperArm').translation
            local=D.to_3x3().inverted()@a;el=math.atan2(local.z,math.hypot(local.x,local.y))
            lift=max(0,el+math.radians(15))*.8
            n=f'Pauldron_{side}';B=rig.data.bones[n].matrix_local
            R=D.to_3x3()@Matrix.Rotation(lift*sgn,3,Vector((0,-1,0)))@B.to_3x3()
            M=R.to_4x4();M.translation=D@B.translation;armik.set_world(rig,n,M)
            pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=out)
