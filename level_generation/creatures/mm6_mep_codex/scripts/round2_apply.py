import bpy,sys,runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round2_head_lod{level}.blend'));b=bpy.data.objects['Body']
 for mat in b.data.materials:
  prefix='mep_head' if 'Head' in mat.name else 'mep_staff' if 'Staff' in mat.name else 'mep'
  for node in mat.node_tree.nodes:
   if node.type!='TEX_IMAGE' or not node.image:continue
   name=node.image.name.lower();key='basecolor' if 'base' in name else 'normal' if 'normal' in name else 'orm' if 'orm' in name else None
   if key:
    im=bpy.data.images.load(str(P/f'textures/lod{level}/{prefix}_{key}.png'),check_existing=False);im.colorspace_settings.name='sRGB' if key=='basecolor' else 'Non-Color';node.image=im;im.pack()
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/final_lod{level}.blend'))
 if level==0:
  b.name=b.data.name='Mep';bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_mep.blend'))
runpy.run_path(str(P/'scripts/round1_export.py'),run_name='__main__')
for name in ['finalize_runtime.py','viewer_tiers.py','prepare_review.py']:subprocess.run(['/usr/bin/python3',str(P/'scripts'/name)],check=True)

(P/'export/mm6_mep.blend').chmod(0o644)
