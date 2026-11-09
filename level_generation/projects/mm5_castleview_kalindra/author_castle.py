"""Original Kalindra court, arch and polygonal royal towers with native-scale artwork."""
import math


def royal_tower(author,panels,component,palette):
    ring=component['polygon']
    x0,y0,x1,y1=component['bounds']
    cx,cy=(x0+x1)/2,(y0+y1)/2
    floor,top=component['eave'],component['top']
    inner=[(cx+(x-cx)*(1-48/((x1-x0)/2)),cy+(y-cy)*(1-48/((y1-y0)/2))) for x,y in ring]
    wall={**palette,'window':palette['towerWindow']}
    author.panel(panels,[(*p,-64) for p in reversed(ring)],palette['plainStone'])
    for i,a in enumerate(ring):
        j=(i+1)%len(ring)
        b=ring[j]
        author.wall(panels,a,b,-64,0,wall,windows=False)
        author.wall(panels,a,b,0,floor,wall,window_levels=component['windowLevels'])
        author.panel(panels,[(*a,floor),(*b,floor),(*b,top-32),(*a,top-32)],palette['plainStone'])
        author.panel(panels,[(*a,top-32),(*b,top-32),(*b,top),(*a,top)],palette['trim'])
        author.panel(panels,[(*inner[j],floor),(*inner[i],floor),(*inner[i],top),(*inner[j],top)],
                     palette['plainStone'])
        author.panel(panels,[(*a,top),(*b,top),(*inner[j],top),(*inner[i],top)],palette['plainStone'])
    author.panel(panels,[(*p,floor) for p in inner],palette['floor'])
    # Closed stone belts project from the shaft without coplanar overlays.
    outer=[(cx+(x-cx)*(1+16/((x1-x0)/2)),cy+(y-cy)*(1+16/((y1-y0)/2))) for x,y in ring]
    for lo in [512,1536,2560]:
        for i,a in enumerate(outer):
            j=(i+1)%len(ring)
            b=outer[j]
            author.panel(panels,[(*a,lo),(*b,lo),(*b,lo+32),(*a,lo+32)],palette['trim'])
            author.panel(panels,[(*ring[i],lo),(*ring[j],lo),(*b,lo),(*a,lo)],palette['plainStone'])
            author.panel(panels,[(*a,lo+32),(*b,lo+32),(*ring[j],lo+32),(*ring[i],lo+32)],palette['plainStone'])


def checked_box(author,panels,bounds,key,building,model,kind):
    face=len(panels)+(5 if kind=='walking surface' else 4)
    author.box(panels,bounds,key)
    building.setdefault('geometryChecks',[]).append({'model':model,'faces':[face],'kind':kind})


def entry_arch(author,panels,component,palette,building):
    x0,y0,x1,y1=component['bounds']
    half=component['openingWidth']/2
    spring,top=component['eave'],component['top']
    name='kalindra_'+component['id']
    for bounds in [[x0,y0,-64,-half,y1,top],[half,y0,-64,x1,y1,top]]:
        checked_box(author,panels,bounds,palette['wall'],building,name,'buried pier foot')
    curve=[(-half*math.cos(i*math.pi/12),spring+component['archRise']*math.sin(i*math.pi/12))
           for i in range(13)]
    for (a,za),(b,zb) in zip(curve,curve[1:]):
        author.panel(panels,[(a,y0,za),(b,y0,zb),(b,y0,top),(a,y0,top)],palette['wall'])
        author.panel(panels,[(b,y1,zb),(a,y1,za),(a,y1,top),(b,y1,top)],palette['wall'])
        author.panel(panels,[(a,y1,za),(b,y1,zb),(b,y0,zb),(a,y0,za)],palette['plainStone'])
    author.panel(panels,[(-half,y0,top),(half,y0,top),(half,y1,top),(-half,y1,top)],palette['plainStone'])
    author.box(panels,[x0-8,y0-8,top,x1+8,y1+8,top+32],palette['trim'])


def paving(author,panels,component,palette,building):
    x0,y0,x1,y1=component['bounds']
    checked_box(author,panels,[x0,y0,-32,x1,y1,component['top']],palette['floor'],building,
                'kalindra_'+component['id'],'walking surface')


def fittings(author,panels,building,palette):
    name='kalindra_service_details'
    for detail in building['details']:
        x0,y0,z0,x1,y1,z1=detail['bounds']
        # Trestle benches face inward from unequal sides of the court.
        for y in [y0+24,y1-48]:
            checked_box(author,panels,[x0+8,y,z0,x1-8,y+24,64],palette['plainStone'],building,
                        name,'buried bench foot')
        author.box(panels,[x0,y0,64,x1,y1,80],palette['trim'])
        back=x0 if detail['id'].startswith('south') else x1-16
        for y in [y0+24,y1-48]:
            author.box(panels,[back,y,80,back+16,y+24,z1],palette['trim'])
        author.box(panels,[back,y0,120,back+16,y1,152],palette['trim'])
    # The painted crown is an original regional motif, not the Dragon Hunters' heraldry.
    for cx in [-512,640]:
        author.box(panels,[cx-72,-12,548,cx+72,0,564],palette['trim'])
        author.panel(panels,[(cx-64,-6,296),(cx+64,-6,296),(cx+64,-6,552),(cx-64,-6,552)],
                     palette['banner'],[(0,0),(1,0),(1,1),(0,1)])
