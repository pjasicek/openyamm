import bpy,sys,json
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
for row in json.loads((P/'work/round4_hand_corrections.json').read_text()):
 level=row['lod'];bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));ob=bpy.data.objects['Body'];tree=KDTree(len(ob.data.vertices))
 for v in ob.data.vertices:tree.insert(v.co,v.index)
 tree.balance();count=0
 for item in row['vertices']:
  matches=tree.find_range(Vector(item['rest']),.00001);assert matches,(level,item['rest'])
  for co,i,d in matches:ob.data.vertices[i].co+=Vector(item['delta']);count+=1
 ob.data.update();C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));print('APPLIED_HAND_FIT',level,count,flush=True)
