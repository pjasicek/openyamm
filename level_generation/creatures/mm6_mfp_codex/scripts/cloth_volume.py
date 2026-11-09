"""Close open garment rims for nearest-surface classification, excluding passage through openings."""
from mathutils.bvhtree import BVHTree
import numpy as np

def capped_tree(positions, faces, boundary):
 points=positions.tolist();polygons=list(faces);edges=set(tuple(sorted(e))for e in boundary)
 while edges:
  edge=edges.pop();component=set(edge);changed=True
  while changed:
   changed=False
   for e in list(edges):
    if component.intersection(e):component.update(e);edges.remove(e);changed=True
  ring=[e for e in boundary if e[0]in component and e[1]in component]
  center=len(points);points.append(positions[list(component)].mean(0).tolist())
  polygons.extend((i,j,center)for i,j in ring)
 return BVHTree.FromPolygons(points,polygons)
