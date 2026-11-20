"""Fit the coarse belt feather bridge below the near mesh envelope at shield recovery."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod3.blend'));C.activate('Attack',64/48);r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];n='Feather_B_Pelvis';skin=r.pose.bones[n].matrix@r.data.bones[n].matrix_local.inverted();delta=skin.to_3x3().inverted()@Vector((-.33080527,-.31855223,.88830870))*-.023
points=np.array([[.016787528,-.229767326,.944372002],[.09515392,-.211520246,.981611365],[.145977695,-.065724787,1.035356737]])
ids=[]
for v in body.data.vertices:
 if np.linalg.norm(points-np.array(v.co),axis=1).min()<.00001:v.co+=delta;ids.append(v.index)
assert ids
C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_lod3.blend'))
(P/'review/round3_far_feathers.json').write_text(json.dumps({'lod':3,'vertices':ids,'rest_delta':list(delta),'maximum_move_mm':delta.length*1000,'reason':'Coarse triangular belt-feather bridge exceeded the near envelope at shield recovery; lower the three corners without changing topology.'},indent=2))
