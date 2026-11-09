import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import search_reduction as S,reduction_common as C,reduction_bake as B
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'))
for im in bpy.data.images:
 if im.source=='FILE'and im.filepath and Path(bpy.path.abspath(im.filepath)).is_file():
  if im.packed_file:im.unpack(method='REMOVE')
  im.reload()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduction_master.blend'))
for candidate,level in [('body_lod0_5',0),('body_lod1_6',1),('body_lod1_18',1)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/reduction/{candidate}.blend'));C.reset();obj=bpy.data.objects['Body'];tex=P/f'work/projection/{candidate}_textures';B.bake(obj,tex);subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(tex)],check=True);dest=P/f'work/projection/{candidate}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));S.render(P/f'review/projection/{candidate}','body',level,tex)
