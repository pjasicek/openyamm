"""Original fortified Western Tower shaft, closed terrace and crenellated crown."""


def shaft(author, panels, component, palette, doors):
    x0,y0,x1,y1=component['bounds']
    floor=component['eave']
    top=component['top']
    ring=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    author.panel(panels,[(*p,-64) for p in reversed(ring)],palette['stone'])
    # Use the existing Garrote barred-aperture art at sparse upper levels.
    walls={**palette,'window':'t18a01b'}
    for i,a in enumerate(ring):
        b=ring[(i+1)%4]
        author.wall(panels,a,b,-64,0,walls,windows=False)
        author.wall(panels,a,b,0,floor,walls,doors,front=i==0,
                    window_levels=component['windowLevels'])
    author.panel(panels,[(*p,floor) for p in ring],palette['terrace'])
    # Projected masonry courses are closed on both horizontal faces; no coplanar facade overlay.
    outer=[(x0-16,y0-16),(x1+16,y0-16),(x1+16,y1+16),(x0-16,y1+16)]
    for lo in [480,1248,2016,floor-48]:
        hi=lo+32
        for i,a in enumerate(outer):
            j=(i+1)%4
            b=outer[j]
            author.panel(panels,[(*a,lo),(*b,lo),(*b,hi),(*a,hi)],palette['stone'])
            author.panel(panels,[(*ring[i],lo),(*ring[j],lo),(*b,lo),(*a,lo)],palette['stone'])
            author.panel(panels,[(*a,hi),(*b,hi),(*ring[j],hi),(*ring[i],hi)],palette['stone'])
    # Continuous waist-high safety wall, taller corner/alternating merlons above it.
    sill=floor+128
    thickness=48
    for bounds in [[x0,y0,floor,x1,y0+thickness,sill],
                   [x0,y1-thickness,floor,x1,y1,sill],
                   [x0,y0+thickness,floor,x0+thickness,y1-thickness,sill],
                   [x1-thickness,y0+thickness,floor,x1,y1-thickness,sill]]:
        author.box(panels,bounds,palette['stone'])
    # End merlons join around corners; internal opposite faces are not visible.
    for y in [y0,y1-thickness]:
        for x in [x0,x0+256,x0+512,x0+768,x0+1024,x1-128]:
            author.box(panels,[x,y,sill,x+128,y+thickness,top],palette['stone'])
    for x in [x0,x1-thickness]:
        for y in [y0+thickness,y0+288,y0+544,y0+800,y0+1056,y1-128]:
            end=min(y+128,y1-thickness)
            author.box(panels,[x,y,sill,x+thickness,end,top],palette['stone'])
