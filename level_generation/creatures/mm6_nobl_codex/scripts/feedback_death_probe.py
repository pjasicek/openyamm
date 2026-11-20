from pathlib import Path
import sys
p=Path(__file__).resolve().parents[1]
exec(compile((p/'scripts/feedback_tabard.py').read_text().split('report={}')[0],str(p/'scripts/feedback_tabard.py'),'exec'))
use(bpy.data.actions['Death'])
for f in [8,16,24,35,55]:
 sc.frame_set(f);pm=r.pose.bones['B_Pelvis'].matrix.copy();P=posed();tree=BVHTree.FromPolygons(P.tolist(),faces)
 for deg in [-120,-90,-60,-30,0,30,60,90,120]:
  X=vertices(math.radians(deg),pm)
  depths=[]
  for i,pt in zip(C,X):
   if co[i,2]>.975:continue
   loc,normal,face,dist=tree.find_nearest(Vector(pt),.1)
   if loc is not None and inside(tree,pt):depths.append(dist)
  print('DEATH_PROBE',f,deg,'zrange',np.round([X[:,2].min(),X[:,2].max()],3).tolist(),'floor_count',int((X[:,2]<-.001).sum()),'inside',len(depths),'depthmax',round(max(depths,default=0),3))
