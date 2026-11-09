"""Two elastic bow limbs; the native spare-arrow carrier follows the lower limb."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_complete.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Attack'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
scene.frame_set(25);bm=rig.pose.bones['Bow'].matrix.copy();local=bm.inverted()@rig.pose.bones['B_R_Hand'].head
direction=1 if local.y>0 else -1
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();rest=rig.data.bones['Bow'].matrix_local.copy()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,z in [('BowUpper',.10),('BowLower',-.10)]:
    assert name not in rig.data.edit_bones
    b=rig.data.edit_bones.new(name);M=rest@Matrix.Translation((0,0,z))
    b.head=M.translation;b.tail=b.head+M.to_3x3().col[1]*.12;b.align_roll(M.to_3x3().col[2]);b.parent=rig.data.edit_bones['Bow']
bpy.ops.object.mode_set(mode='OBJECT')
for name in ['BowUpper','BowLower']:body.vertex_groups.new(name=name);rig.pose.bones[name].rotation_mode='QUATERNION'
piece=body.data.attributes['piece'];counts={'BowUpper':0,'BowLower':0}
for v in body.data.vertices:
    pid=piece.data[v.index].value
    if pid not in [4000,4004]:continue
    z=(rest.inverted()@v.co).z;name='BowUpper'if z>0 else'BowLower'
    w=1 if pid==4004 else float(np.clip((abs(z)-.08)/.14,0,1))
    if not w:continue
    body.vertex_groups['Bow'].remove([v.index])
    if w<1:body.vertex_groups['Bow'].add([v.index],1-w,'REPLACE')
    body.vertex_groups[name].add([v.index],w,'REPLACE');counts[name]+=1
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
release=float(scene['attack_impact_seconds'])*30
for a in bpy.data.actions:
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    frames=np.arange(0,float(a.frame_range[1])+.01,.125)if a.name=='Attack'else[0,float(a.frame_range[1])]
    for f in frames:
        w=smooth((f-18)/3)*(1-smooth((f-release+.5)/.5))if a.name=='Attack'else 0
        for name,sign in [('BowUpper',-1),('BowLower',1)]:
            b=rig.pose.bones[name];b.rotation_quaternion=Quaternion((1,0,0),direction*sign*math.radians(7)*w)
            b.keyframe_insert('rotation_quaternion',frame=float(f))
scene['bow_tip_bones']=json.dumps(['BowUpper','BowLower'])
scene['bow_flex_degrees']=7
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_complete.blend'))
(P/'work/bow_flex.json').write_text(json.dumps({'degrees':7,'draw_direction':direction,'weighted_vertices':counts},indent=2));print('BOW FLEX',counts)
