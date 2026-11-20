"""Original, modest outdoor fittings for the source-backed countryside retreats."""
import math


def details(author, panels, building, palette, work):
    for detail in building['details']:
        x0,y0,z0,x1,y1,z1=detail['bounds']
        if detail['id']=='study_ledge':
            # Wall-supported shelf below the side window; no legs on the sloping shore.
            author.box(panels,[x0,y0,112,x1,y1,128],work['wood'])
            for y in [y0+16,y1-32]:
                author.box(panels,[x0,y,96,x0+24,y+16,112],work['wood'])
        elif detail['id']=='animal_trough':
            # Low masonry vessel, with a closed bottom and water below its thick lip.
            author.box(panels,[x0,y0,z0,x1,y1,24],palette['stone'])
            for bounds in [[x0,y0,24,x1,y0+12,z1],[x0,y1-12,24,x1,y1,z1],
                           [x0,y0+12,24,x0+12,y1-12,z1],
                           [x1-12,y0+12,24,x1,y1-12,z1]]:
                author.box(panels,bounds,palette['stone'])
            author.panel(panels,[(x0+12,y0+12,48),(x1-12,y0+12,48),
                                 (x1-12,y1-12,48),(x0+12,y1-12,48)],work['water'])
        elif detail['id']=='astronomy_dial':
            cx,cy=(x0+x1)/2,(y0+y1)/2
            author.box(panels,[x0,y0,z0,x1,y1,16],palette['stone'])
            author.box(panels,[cx-20,cy-20,16,cx+20,cy+20,112],palette['stone'])
            author.box(panels,[cx-36,cy-36,112,cx+36,cy+36,128],work['metal'])
            # A small vertical graduated-looking hoop and fixed sighting bar.
            # Explicit annular faces give both sides thickness in native rendering.
            rings=[]
            for y,radius in [(cy-4,44),(cy-4,38),(cy+4,44),(cy+4,38)]:
                rings.append([(cx+radius*math.cos(i*math.tau/16),y,
                               172+radius*math.sin(i*math.tau/16)) for i in range(16)])
            a,b,c,d=rings
            for i in range(16):
                j=(i+1)%16
                for points in [[a[i],a[j],b[j],b[i]],[c[j],c[i],d[i],d[j]],
                               [a[j],a[i],c[i],c[j]],[b[i],b[j],d[j],d[i]]]:
                    author.panel(panels,points,work['metal'])
            author.box(panels,[cx-40,cy-3,169,cx+40,cy+3,175],work['metal'])


def altar(author, prop, palette):
    panels=[]
    author.box(panels,[-160,-80,-32,160,80,16],palette['stone'])
    for x in [-120,88]:
        author.box(panels,[x,-48,16,x+32,48,112],palette['column'])
    author.box(panels,[-144,-64,112,144,64,128],palette['stone'])
    # Three actual shallow recesses, not painted circles or already-restored statues.
    # Build the top from nonoverlapping strips surrounding the socket openings.
    for bounds in [[-144,-64,128,144,-24,144],[-144,24,128,144,64,144]]:
        author.box(panels,bounds,palette['rim'])
    previous=-144
    for center in [-88,0,88]:
        left,right=center-24,center+24
        author.box(panels,[previous,-24,128,left,24,144],palette['rim'])
        author.box(panels,[left,-24,128,right,24,132],palette['stone'])
        previous=right
    author.box(panels,[previous,-24,128,144,24,144],palette['rim'])
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],
                 'label':prop['title'],'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
