from pathlib import Path
import sys,bpy
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import pbr_round3 as pbr
setup=pbr.setup
def normal_setup(body,rig,variant,tier,pixels=700,lod=0):
 result=setup(body,rig,variant,tier,pixels,lod)
 for node in body.data.materials[0].node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image.filepath.endswith('knight_normal_l3.png'):
   node.image=bpy.data.images.load(str(P/'work/round3/lod3_source_normal_256.png'));node.image.colorspace_settings.name='Non-Color'
 return result
pbr.setup=normal_setup
pbr.render('low','a','lod3_source_normal_256_probe',88,3,views=range(8))
