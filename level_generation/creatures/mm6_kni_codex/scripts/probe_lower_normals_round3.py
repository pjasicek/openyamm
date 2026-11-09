from pathlib import Path
import sys,bpy
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import pbr_round3 as pbr
setup=pbr.setup
def normal_setup(body,rig,variant,tier,pixels=700,lod=0):
 result=setup(body,rig,variant,tier,pixels,lod)
 for node in body.data.materials[0].node_tree.nodes:
  if node.type=='TEX_IMAGE' and 'knight_normal_l' in node.image.filepath:
   node.image=bpy.data.images.load(str(P/'work/round3/high_normal.png'));node.image.colorspace_settings.name='Non-Color'
 return result
pbr.setup=normal_setup
for lod,pixels in [(1,550),(2,220)]:pbr.render('low','a',f'lod{lod}_original_normal_probe',pixels,lod,views=range(8))
