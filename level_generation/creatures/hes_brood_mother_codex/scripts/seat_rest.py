"""Lift returned resting claws out of the belly, preserving measured arm lengths and skinning."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
from arm_contact import pin_arm
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];report={}
for side,offset in [('L',(.13,.13,.06)),('R',(-.16,-.16,.06))]:
 hand=rig.pose.bones[f'B_{side}_Hand'];target=hand.head+Vector(offset)
 pin_arm(rig,side,target,hand.matrix.to_quaternion())
 report[side]={'wrist_offset_m':offset,'new_wrist_m':list(hand.head)}
for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH':continue
 bpy.context.view_layer.objects.active=ob
 modifier=next(m for m in ob.modifiers if m.type=='ARMATURE')
 bpy.ops.object.modifier_apply(modifier=modifier.name)
 modifier=ob.modifiers.new('Armature','ARMATURE');modifier.object=rig
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
(P/'review/rest_contact_fit.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v2.blend'))
print(json.dumps(report))
