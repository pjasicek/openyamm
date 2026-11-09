import bpy,sys,collections
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
m=bpy.data.objects['Body'].data
pv=[x.value for x in m.attributes['piece'].data]
print('FACE MATS',collections.Counter(f.material_index for f in m.polygons if pv[f.vertices[0]]==1))
for mat in m.materials:
 if mat:mat.diffuse_color=(.65,.65,.65,1)
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/clay_head'),1.49,.35,views=('front','three_quarter'),resolution=(600,600))

from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
tree=BVHTree.FromPolygons([v.co for v in m.vertices],[tuple(f.vertices) for f in m.polygons])
hits=set()
for x in np.linspace(-.04,-.015,15):
 for z in np.linspace(1.475,1.495,15):
  loc,n,idx,d=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
  if idx is not None and pv[m.polygons[idx].vertices[0]]!=1:hits.add(idx)
for i in sorted(hits):
 f=m.polygons[i];print('WRONG SURFACE',i,'piece',pv[f.vertices[0]],'material',f.material_index,[tuple(m.vertices[v].co) for v in f.vertices])
