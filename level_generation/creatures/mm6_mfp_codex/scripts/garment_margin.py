"""Keep simplified lower garment surfaces 2 mm outside the original cloth shell."""
import bpy,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]

def clear_garment(body):
 with bpy.data.libraries.load(str(P/'work/rig_textured.blend'),link=False)as(src,dst):dst.objects=['Body']
 ref=dst.objects[0];pv=np.array([x.value for x in ref.data.attributes['piece'].data]);tree=BVHTree.FromPolygons([v.co[:]for v in ref.data.vertices],[f.vertices[:]for f in ref.data.polygons if pv[f.vertices[0]]==1]);bpy.data.objects.remove(ref,do_unlink=True);parts=body.data.attributes['piece'].data;moved=[]
 for v in body.data.vertices:
  if parts[v.index].value!=1:continue
  margin=.002*np.clip((.85-v.co.z)/.20,0,1)
  if margin==0:continue
  loc,n,_,d=tree.find_nearest(v.co);signed=(v.co-loc).dot(n);shift=max(0,float(margin-signed));v.co+=n*shift;moved.append(shift)
 body.data.update();return {'vertices_moved':sum(x>1e-7 for x in moved),'max_offset_m':max(moved,default=0),'target_clearance_m':.002}
