import bpy
from pathlib import Path
root=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/detail_rebuild_01')
img=bpy.data.images['Goblin_Low_DetailNormal_2048']
if img.packed_file:img.unpack(method='REMOVE')
img.filepath=str(root/'body_pouch_plates_normal.png');img.reload();img.pack()
exec(Path('/tmp/openyamm_export_goblin_detail.py').read_text())
