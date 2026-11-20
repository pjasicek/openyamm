"""Render each motion at four phases plus independent stress poses."""
import bpy
import json
import os
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'scripts'))
import common as C
import posing as P
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/anim_v1.blend'))
rig=bpy.data.objects['Hound_Rig']
mesh=bpy.data.objects['Hound']
sc=bpy.context.scene
out=PROJECT/'review/motion'
out.mkdir(exist_ok=True)
cells=[]
for action in bpy.data.actions:
    rig.animation_data.action=action
    if action.slots: rig.animation_data.action_slot=action.slots[0]
    for k in range(4):
        frame=round(action.frame_range[1]*k/3)
        sc.frame_set(frame)
        name=f'{action.name}_{frame}'
        C.render_ortho((3,-3,1.8),(0,-.05,.45),3.2,str(out/f'{name}.png'),
                       res=(600,400),show=['Hound'],bg=(.12,.13,.15))
        cells.append({'name':name,'file':f'review/motion/{name}.png','row':action.name})
rig.animation_data.action=None
for name,ops in {
 'rest':[],
 'stride':[('Thigh_L','X',35),('Shin_L','X',-30),('UpperArm_R','X',35),('ForeArm_R','X',-25)],
 'rear':[('Spine1','X',-35),('Spine2','X',-15),('Neck1','X',15)],
 'tail_head':[('Tail1','X',25),('Tail2','Z',20),('Tail3','Z',25),('Tail4','Z',25),
              ('Neck1','Z',20),('Head','X',20)],
 'roll':[('Spine1','Y',80),('UpperArm_L','X',30),('Thigh_R','X',-20)],
 'jaw':[('Jaw','X',-18)],
}.items():
    P.reset(rig)
    for bone,axis,degrees in ops: P.rotate_world(rig,bone,axis,degrees)
    for view,loc in [('side',(3,0,.7)),('quarter',(3,-3,1.8))]:
        tag=f'stress_{name}_{view}'
        C.render_ortho(loc,(0,-.05,.45),3.2,str(out/f'{tag}.png'),
                      res=(600,400),show=['Hound'],bones=name=='rest',bg=(.12,.13,.15))
        cells.append({'name':tag,'file':f'review/motion/{tag}.png','row':'stress_'+name})
(out/'index.json').write_text(json.dumps(cells,indent=2)+'\n')
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
