"""Local m556 pose controls; reuse the existing measured two-bone solver."""
import sys,math,bpy
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'mm6_rat_claude/scripts'))
from posing import reset,rotate_world,aim_bone,two_bone_ik

def orient_hand(rig,side,direction):
 item=rig.pose.bones['Sword' if side=='L' else 'Shield'];hand=rig.pose.bones['Hand_'+side]
 q=(item.tail-item.head).normalized().rotation_difference(Vector(direction).normalized());h=hand.head.copy()
 hand.matrix=Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h)@hand.matrix
 bpy.context.view_layer.update()

def arms(rig,sword=(.15,-.205,.57),shield=(-.12,-.205,.61),blade=(.10,-.36,.93)):
 for side,target in [('L',sword),('R',shield)]:
  sign=1 if side=='L' else -1
  two_bone_ik(rig,'UpperArm_'+side,'ForeArm_'+side,target,(sign*.34,.03,.48))
  orient_hand(rig,side,blade if side=='L' else (0,-1,.08))

def base_pose(rig,t=0,fast=False):
 reset(rig);phase=2*math.pi*t/.625
 # Two wingbeats in the native flight loop, body and trailing parts lag the power stroke.
 bob=.008*(1-math.cos(2*phase));rig.pose.bones['Root'].location=rig.data.bones['Root'].matrix_local.to_3x3().transposed()@Vector((0,0,bob))
 rotate_world(rig,'Thorax','X',4 if fast else 0)
 for side,sg in [('L',1),('R',-1)]:
  rotate_world(rig,'WingRoot_'+side,'Y',sg*(27-48*math.cos(2*phase)))
  rotate_world(rig,'WingRoot_'+side,'X',-12+8*math.sin(2*phase))
  rotate_world(rig,'WingRoot_'+side,'Z',sg*30)
  rotate_world(rig,'WingFlex_'+side,'Y',sg*5*math.sin(2*phase-.55))
  rotate_world(rig,'HindCoxa_'+side,'X',-7+3*math.sin(phase-.7))
  rotate_world(rig,'HindFemur_'+side,'Y',sg*(12+3*math.sin(phase-.8)))
  rotate_world(rig,'HindTarsus_'+side,'X',5*math.sin(phase-1.1))
  rotate_world(rig,'MidFemur_'+side,'Y',sg*8)
  rotate_world(rig,'MidTibia_'+side,'X',4*math.sin(phase+.5))
  for i in range(1,4):rotate_world(rig,f'Antenna{i}_{side}','X',1.5*math.sin(phase-i*.45))
 for i in range(1,5):rotate_world(rig,'Abdomen'+str(i),'X',1.5*math.sin(phase-i*.5))
 arms(rig)
 bpy.context.view_layer.update()
