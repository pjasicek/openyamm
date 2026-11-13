import sys;sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/tools')
from geom import *
tol=float(sys.argv[1])
for a in sys.argv[2:]:
    si=int(a)
    ls=raster_outline(sector_polys(si),tol=tol)
    for l in ls:
        print(f"S{si} n={len(l)} area={area2(l)/1e3:.0f}k", [[int(x),int(y)] for x,y in l])
