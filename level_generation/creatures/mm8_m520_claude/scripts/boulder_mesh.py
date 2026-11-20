"""Normalize and close the generated boulder while preserving its UV corners."""
import bpy,bmesh,numpy as np
from mathutils import Matrix

def prepare(rock):
 coords=np.array([rock.matrix_world@v.co for v in rock.data.vertices]);lo,hi=coords.min(0),coords.max(0)
 coords=(coords-(lo+hi)/2)*np.array([.58,.40,.38])/(hi-lo)
 rock.matrix_world=Matrix.Identity(4)
 for v,c in zip(rock.data.vertices,coords):v.co=c
 bm=bmesh.new();bm.from_mesh(rock.data)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-5)
 # A single triangular flap shares one edge with the closed stone.
 flaps=[f for f in bm.faces if sum(e.is_boundary for e in f.edges)==2 and any(len(e.link_faces)>2 for e in f.edges)]
 assert len(flaps)==1,('unexpected stone flap count',len(flaps))
 bmesh.ops.delete(bm,geom=flaps,context='FACES')
 boundary=[e for e in bm.edges if e.is_boundary]
 if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bmesh.ops.triangulate(bm,faces=list(bm.faces))
 assert all(e.is_manifold for e in bm.edges),('boulder topology',sum(not e.is_manifold for e in bm.edges))
 assert bm.calc_volume(signed=True)>0,'boulder winding'
 print('BOULDER_CLEAN',len(bm.verts),len(bm.faces),'volume',bm.calc_volume(signed=True),flush=True)
 bm.to_mesh(rock.data);bm.free();rock.data.update()
