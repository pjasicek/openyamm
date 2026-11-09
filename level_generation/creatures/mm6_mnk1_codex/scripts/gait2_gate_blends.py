"""Gate copies for the gait2 clips: each LOD master (export/mm6_mnk1.blend, work/review4_lod1-3.blend) with Walk2/Run2
from work/gait2.blend standing in for Walking/Running, so the project's own gates (review4_penetration.py,
gates_dense.py, review4_anatomy.py, g6_contacts.py) run unchanged on the new clips. Writes work/gait2/gate_lod<N>.blend."""
import bpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
SRC=os.environ.get('G2_SRC','work/gait2.blend');LEVELS=[int(x) for x in os.environ.get('G2_LEVELS','0,1,2,3').split(',')];ONLY=os.environ.get('G2_ONLY_GAITS')
for level,src in enumerate(['export/mm6_mnk1.blend','work/review4_lod1.blend','work/review4_lod2.blend','work/review4_lod3.blend']):
 if level not in LEVELS:continue
 bpy.ops.wm.open_mainfile(filepath=str(p/src))
 for n in ['Walking','Running']:bpy.data.actions.remove(bpy.data.actions[n])
 with bpy.data.libraries.load(str(p/SRC),link=False) as (src_data,dst):dst.actions=['Walk2','Run2']
 for a in dst.actions:a.use_fake_user=True
 bpy.data.actions['Walk2'].name='Walking';bpy.data.actions['Run2'].name='Running'
 r=bpy.data.objects['Rig'];r.animation_data.action=None
 if ONLY:
  for a in list(bpy.data.actions):
   if a.name not in ('Walking','Running'):bpy.data.actions.remove(a)
 bpy.ops.wm.save_as_mainfile(filepath=str(p/os.environ.get('G2_GATE_OUT',f'work/gait2/gate_lod{level}.blend')))
 print('GATE_BLEND',level,[a.name for a in bpy.data.actions])
