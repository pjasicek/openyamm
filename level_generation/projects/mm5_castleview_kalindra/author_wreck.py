"""Independent open broken hull, exposed frames, snapped mast and small torn sail."""
from author_camps import beam, cloth

# Native units: longitudinal station, sheer half-width, keel Z and rail Z.
STATIONS = [(-640,112,-8,192),(-480,176,-24,176),(-160,224,-36,160),
            (160,208,-48,144),(440,144,-56,160),(640,12,-32,216)]


def author_wreck(author,prop,palette):
    panels = []

    def surface(points,key,vertical=False):
        a=[points[1][i]-points[0][i] for i in range(3)]
        b=[points[2][i]-points[0][i] for i in range(3)]
        normal=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
        axis=max(range(3),key=lambda i:abs(normal[i]))
        # Both triangles share one grain projection. Planks run along the hull; mast grain runs upward.
        uv_axes=([(1,2),(0,2),(0,1)] if vertical else [(2,1),(2,0),(0,1)])[axis]
        for i in range(1,len(points)-1):
            triangle=[points[0],points[i],points[i+1]]
            author.panel(panels,triangle,palette[key],[(p[uv_axes[0]]/64,p[uv_axes[1]]/64) for p in triangle])

    def board(outer,inner,key='wood',open_edges=()):
        # Explicit triangles keep all curved/tapered hull panels planar for the native compiler.
        surface(outer,key)
        surface(list(reversed(inner)),key)
        for i in range(4):
            if i in open_edges: continue
            j=(i+1)%4
            surface([outer[j],outer[i],inner[i],inner[j]],key)

    def section(station,side,fraction,inset=0):
        y,width,bottom,top = station
        half_width=width*(.34+.66*fraction)
        # Thin the planking at the pointed bow so opposite inner skins cannot cross the centerline.
        return (side*(half_width-min(inset,half_width*.6)),y,bottom+(top-bottom)*fraction)

    # Three strakes curve around the narrow keel. Two missing upper boards expose the midship frames.
    for side in [-1,1]:
        for segment,(a,b) in enumerate(zip(STATIONS,STATIONS[1:])):
            for row in range(3):
                if (side,segment,row) in [(-1,2,2),(1,3,2)]: continue
                low,high = row/3,(row+1)/3
                outer=[section(a,side,low),section(b,side,low),
                       section(b,side,high),section(a,side,high)]
                inner=[section(a,side,low,12),section(b,side,low,12),
                       section(b,side,high,12),section(a,side,high,12)]
                if side<0: outer.reverse();inner.reverse()
                # The transom closes this joint. A second coplanar end cap causes a black overlap strip.
                board(outer,inner,open_edges=(3,) if segment==0 else ())
    # Long narrow bottom, not a filled deck; water can remain visible inside the broken boat.
    for a,b in zip(STATIONS,STATIONS[1:]):
        surface([section(a,-1,0),section(a,1,0),section(b,1,0),section(b,-1,0)],'wood')
    # Stern transom is the reachable bank-side search contact.
    a=STATIONS[0]
    outer=[section(a,-1,0),section(a,1,0),section(a,1,1),section(a,-1,1)]
    inner=[(x,y+12,z) for x,y,z in outer]
    board(outer,inner)
    # Unequal exposed ribs support the open hull and surviving seating.
    for station in STATIONS[1:-1]:
        y,width,bottom,top=station
        for side in [-1,1]:
            beam(author,panels,(side*width*.32,y,bottom+8),
                 (side*(width-18),y,top-8),18,palette['rib'])
        beam(author,panels,(-width*.32,y,bottom+8),(width*.32,y,bottom+8),18,palette['rib'])
    for y,width,z in [(-480,152,112),(160,184,80)]:
        author.box(panels,[-width,y-30,z,width,y+30,z+16],palette['wood'])
    # Broken rail remnants reveal splintered ends instead of an unbroken decorative perimeter.
    for points in [[(-224,-160,160),(-219,-60,153),(-224,-160,94)],
                   [(208,160,144),(198,205,156),(208,160,80)]]:
        cloth(author,panels,points,palette['wood'],8)
    # Thick snapped mast with a jagged cap, and its fallen upper spar resting across a surviving rail.
    base=[(-20,12,0),(20,12,0),(20,52,0),(-20,52,0)]
    top=[(36,44,720),(72,44,748),(72,80,716),(36,80,764)]
    surface(list(reversed(base)),'wood')
    for i in range(4):
        j=(i+1)%4
        surface([base[i],base[j],top[j],top[i]],'wood',vertical=True)
    surface(top,'rib')
    beam(author,panels,(40,40,592),(-144,440,166),24,palette['wood'])
    beam(author,panels,(-76,160,608),(112,72,644),18,palette['wood'])
    # Small ragged cloth pieces retain the original torn-sail cue; no full intact sail.
    cloth(author,panels,[(-76,160,608),(32,110,630),(-24,138,444)],palette['cloth'],3)
    cloth(author,panels,[(38,108,632),(112,72,644),(72,90,534)],palette['cloth'],3)
    prop['hullStations']=[list(s) for s in STATIONS]
    prop['nativeGeometryIntent']='Open planked hull, two missing strakes, exposed ribs, snapped mast and torn sail'
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
