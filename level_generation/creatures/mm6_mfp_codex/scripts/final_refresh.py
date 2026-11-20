import bpy,sys,os,json,subprocess,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from bake_reduction import rebake
for name in ['rig_textured','rig_polished']:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work'/f'{name}.blend'))
 for im in bpy.data.images:
  path=Path(bpy.path.abspath(im.filepath))
  if path.parent==P/'textures' and path.exists():
   if im.packed_file:im.unpack(method='REMOVE')
   im.reload()
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work'/f'{name}.blend'))
sel=json.loads((P/'review/reduction_soft/selection.json').read_text())
for level,row in sel.items():
 bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));folder=P/f'work/final_textures/lod{level}';rebake(folder,[1024,512,256,128][int(level)]);subprocess.run(['/usr/bin/python3',str(P/'scripts/bake_tiers.py'),str(folder)],check=True);r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/row['blend']));row['textures']=str(folder)
(P/'review/reduction_soft/selection.json').write_text(json.dumps(sel,indent=2))
runpy.run_path(str(P/'scripts/export_levels.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/final_visual.py'),run_name='__main__')
