"""Fit the native compact pommel so it clears the forearm during the backward fall."""
from pathlib import Path
import bpy,sys,runpy
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/master_reduced.blend'))
rig=bpy.data.objects['Rig'];M=rig.data.bones['Sword'].matrix_local;inv=M.inverted()
for v in bpy.data.objects['SwordMesh'].data.vertices:
 c=inv@v.co
 if c.y<-.085:
  c.x*=.6;c.z*=.6;c.y=-.09+(c.y+.12)*.6;v.co=M@c
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/master_reduced.blend'))
sys.argv=['export_runtime.py'];runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
