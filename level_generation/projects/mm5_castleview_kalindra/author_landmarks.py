"""Original polygonal civic geometry; reference meshes are never imported."""
import math


def polygon_hall(author,panels,component,palette,doors):
    polygon=component['polygon']
    author.panel(panels,[(*p,-64) for p in reversed(polygon)],palette['stone'])
    for i,a in enumerate(polygon):
        b=polygon[(i+1)%len(polygon)]
        author.wall(panels,a,b,-64,0,palette,windows=False)
        author.wall(panels,a,b,0,component['eave'],palette,doors,
                    front=i==0 and a[1]==0 and b[1]==0,window_levels=component.get('windowLevels'))
    x0,y0,x1,y1=component['bounds']
    cx,cy=(x0+x1)/2,(y0+y1)/2
    expand=lambda offset:[(cx+(x-cx)*(1+offset/((x1-x0)/2)),
                           cy+(y-cy)*(1+offset/((y1-y0)/2))) for x,y in polygon]
    eave=component['eave']
    outer=expand(24)
    for i,p in enumerate(outer):
        j=(i+1)%len(outer)
        q=outer[j]
        author.panel(panels,[(*p,eave),(*q,eave),(cx,cy,component['top'])],palette['roof'])
        author.panel(panels,[(*p,eave-16),(*q,eave-16),(*q,eave),(*p,eave)],palette['trim'])
        author.panel(panels,[(*q,eave-16),(*p,eave-16),(*polygon[i],eave-16),
                             (*polygon[j],eave-16)],palette['trim'])
    if component['roof']=='arcane_tower':
        band=expand(16)
        for lower in [512,1024,1536,2048,eave-32]:
            upper=lower+32
            for i,p in enumerate(band):
                j=(i+1)%len(band)
                q=band[j]
                author.panel(panels,[(*p,lower),(*q,lower),(*q,upper),(*p,upper)],palette['stone'])
                author.panel(panels,[(*polygon[i],lower),(*polygon[j],lower),(*q,lower),(*p,lower)],
                             palette['stone'])
                author.panel(panels,[(*p,upper),(*q,upper),(*polygon[j],upper),(*polygon[i],upper)],
                             palette['stone'])


def mok_inscription(author,panels,key):
    """Plain, newly drawn MOK lettering rather than an imported MM8 religious emblem."""
    def stroke(a,b,width=12):
        dx,dz=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dz)
        nx,nz=dz/length*width/2,-dx/length*width/2
        points=[(a[0]-nx,-2,a[1]-nz),(a[0]+nx,-2,a[1]+nz),
                (b[0]+nx,-2,b[1]+nz),(b[0]-nx,-2,b[1]-nz)]
        author.panel(panels,points,key)
    for a,b in [((-144,528),(-144,608)),((-144,608),(-112,558)),
                ((-112,558),(-80,608)),((-80,608),(-80,528)),
                ((80,528),(80,608)),((80,565),(136,608)),((80,565),(144,528))]:
        stroke(a,b)
    outer=[(32*math.cos(i*math.tau/8),568+44*math.sin(i*math.tau/8)) for i in range(8)]
    inner=[(20*math.cos(i*math.tau/8),568+32*math.sin(i*math.tau/8)) for i in range(8)]
    for i in range(8):
        j=(i+1)%8
        author.panel(panels,[(x,-2,z) for x,z in [outer[i],outer[j],inner[j],inner[i]]],key)
