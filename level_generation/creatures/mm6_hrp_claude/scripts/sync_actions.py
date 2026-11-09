"""Bring the final choreography into the three-atlas master and check its real surface contact."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=32;rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(P/'work/anim_v1.blend'),link=False) as (src,dst):dst.actions=src.actions
for a in bpy.data.actions:a.use_fake_user=True
rig.animation_data_create();root=rig.pose.bones['Root'];inv=rig.data.bones['Root'].matrix_local.to_3x3().transposed()
def coords():
 o=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=o.to_mesh();c=np.array([v.co[:] for v in m.vertices]);o.to_mesh_clear();return c
report={}
for a in bpy.data.actions:
 rig.animation_data.action=a;lo,hi=map(round,a.frame_range);minimum=[]
 for f in range(lo,hi+1):
  sc.frame_set(f);c=coords();z=float(c[:,2].min())
  if z<0 or a.name in ['Death','Dead']:
   root.location+=inv@Vector((0,0,-z));root.keyframe_insert('location',frame=f,group='Root')
  minimum.append(z)
 report[a.name]={'source_min_z':min(minimum),'frames':hi-lo+1}
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));(P/'work/final_contact_adjustments.json').write_text(json.dumps(report,indent=2));print('SYNCED',report,flush=True)
