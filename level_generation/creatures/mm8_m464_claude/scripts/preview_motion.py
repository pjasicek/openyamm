"""Inspect the adapted wardrobe under the inherited motions before texture work."""
import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_mfp_codex/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted_garments.blend'));r=bpy.data.objects['Rig'];scene=bpy.context.scene
common.workbench_clay(scene)
for name,frame in [('Standing',0),('Walking',9),('Walking',27),('Running',6),('Hit',12),('Death',38),('Dead',0),('Fidget',30)]:
 r.animation_data.action=bpy.data.actions[name];scene.frame_set(frame)
 common.render_views(str(P/'review'/f'rom_{name}_{frame}'),.84,1.9,views=('three_quarter',),resolution=(520,700))
