"""Original gemsmith trade details, authored in each workshop's local native coordinates."""
import math


def gemsmith_details(author, panels, building, palette, work, sign):
    # A small painted board sits over the ordinary door, below the eave.
    author.box(panels, [-32,-8,256,32,0,320], palette['trim'])
    author.panel(panels, [(-32,-9,256),(32,-9,256),(32,-9,320),(-32,-9,320)],
                 sign, [(0,0),(1,0),(1,1),(0,1)])
    canopy=next(c for c in building['components'] if c['id']=='sorting_canopy')
    x0,y0,x1,y1=canopy['bounds']
    # These are bounded trays of decorative stock on the existing work bench.
    # Leave its long front edge free for a standing worker / future encounter.
    cx=(x0+x1)/2
    tray_width=min(88,(x1-x0-160)/2)
    for index,center in enumerate([cx-tray_width/2-8,cx+tray_width/2+8]):
        left,right=center-tray_width/2,center+tray_width/2
        front,back=y1-112,y1-56
        for bounds in [[left,front,80,right,back,84],
                       [left,front,84,right,front+4,100],
                       [left,back-4,84,right,back,100],
                       [left,front+4,84,left+4,back-4,100],
                       [right-4,front+4,84,right,back-4,100]]:
            author.box(panels,bounds,palette['trim'])
        for offset,dy,size in [(-tray_width*.22,18,7),(tray_width*.18,34,9),(0,22,6)]:
            px,py=center+offset,front+dy
            ring=[(px+size*math.cos(i*math.tau/5),py+size*math.sin(i*math.tau/5),90)
                  for i in range(5)]
            for i in range(5):
                j=(i+1)%5
                points=[ring[i],ring[j],(px+2,py-1,90+size)]
                if index==0:
                    author.panel(panels,points,work['ore'])
                else:
                    author.panel(panels,points,sign,[(.40,.46),(.60,.46),(.5,.65)])
                author.panel(panels,[ring[j],ring[i],(px,py,84)],work['ore'])
    # Small shipping stock fits under the bench, clear of its supporting legs.
    author.box(panels,[cx-28,y1-112,-32,cx+28,y1-56,48],work['crate'])
