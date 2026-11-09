"""Carry a verified prop-only correction into the already measured reduction candidates."""
import bpy,json,hashlib,shutil,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round2/reduction'
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig']
 mesh=([tuple(v.co)for v in body.data.vertices],[tuple(f.vertices)for f in body.data.polygons],[[tuple((g.group,g.weight))for g in v.groups]for v in body.data.vertices])
 curves={}
 for a in bpy.data.actions:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      if a.name=='Death' and fc.data_path.startswith('pose.bones["Staff"]'):continue
      curves[(a.name,fc.data_path,fc.array_index)]=[(tuple(k.co),k.interpolation)for k in fc.keyframe_points]
 return mesh,curves
old=snapshot(W/'unreduced.blend');new=snapshot(P/'work/runtime_master.blend');assert old==new,'Geometry or body/non-death animation changed.'
for suffix in ['blend','glb']:shutil.copy2(W/f'unreduced.{suffix}',W/f'unreduced_before_dense_drop.{suffix}')
shutil.copy2(P/'work/runtime_master.blend',W/'unreduced.blend');shutil.copy2(P/'export/mm6_jak1_runtime_lod0.glb',W/'unreduced.glb')
receipt=json.loads((W/'source.json').read_text());receipt['previous_model_sha256']=receipt['model_sha256'];receipt['model_sha256']=hashlib.sha256((W/'unreduced.glb').read_bytes()).hexdigest();receipt['blend_sha256']=hashlib.sha256((W/'unreduced.blend').read_bytes()).hexdigest();receipt['animation_revision']='Death Staff translation/orientation only; body geometry, skin weights and all other curves exactly equal';receipt['dense_drop_max_depth_m']=.001973317237570882;(W/'source.json').write_text(json.dumps(receipt,indent=2))
for path in sorted(W.glob('step[0-9][0-9].blend')):
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for action in list(bpy.data.actions):bpy.data.actions.remove(action)
 with bpy.data.libraries.load(str(W/'unreduced.blend'),link=False)as(src,dst):dst.actions=src.actions
 for action in dst.actions:action.use_fake_user=True
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('REFRESHED PROP-ONLY REVISION',receipt['model_sha256'],flush=True)
