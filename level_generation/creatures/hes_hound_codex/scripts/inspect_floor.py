"""Inspect which body parts support the draft corpse; produce measured data and a floor view."""
import bpy
import json
import os
import sys
from pathlib import Path
import numpy as np
PROJECT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/anim_v1.blend'))
rig=bpy.data.objects['Hound_Rig'];body=bpy.data.objects['Hound']
rig.animation_data.action=bpy.data.actions['Dead']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
names=[body.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name for v in body.data.vertices]
for name in sorted(set(names)):
    ids=np.array([i for i,n in enumerate(names) if n==name])
    p=co[ids]
    print(name,len(ids),'min',p[p[:,2].argmin()].round(4),'max',p.max(0).round(4),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
