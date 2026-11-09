from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'meshy/boulder_v1/model_urls_glb.glb'));rock=max((o for o in bpy.data.objects if o.type=='MESH'),key=lambda o:len(o.data.polygons));co=np.array([rock.matrix_world@v.co for v in rock.data.vertices]);lo,hi=co.min(0),co.max(0);co=(co-(lo+hi)/2)*np.array([.58,.40,.38])/(hi-lo)
bm=bmesh.new();bm.from_mesh(rock.data)
for v,c in zip(bm.verts,co):v.co=c
print('ROCK',len(bm.verts),len(bm.faces),'boundary',sum(e.is_boundary for e in bm.edges),'nonmanifold',sum(not e.is_manifold for e in bm.edges),'volume',bm.calc_volume(signed=True),'worlddet',rock.matrix_world.determinant())
for mode in ['before','after']:
 if mode=='after':bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 tree=BVHTree.FromBMesh(bm)
 for point in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(.4,0,-.12),(-.4,0,-.12)]:
  hit,n,face,d=tree.find_nearest(Vector(point));print(mode,point,round((Vector(point)-hit).dot(n),4))
