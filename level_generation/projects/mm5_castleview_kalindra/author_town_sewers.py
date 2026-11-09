"""Original low stone casing and metal grille for the five distinct Castleview sewer contacts."""


def author_grate(author, prop, palette):
    panels = []
    geometry(author,panels,prop,palette)
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)


def geometry(author, panels, prop, palette):
    first = len(panels)
    bottom = prop['foundation']['skirtBottomZ']-prop['padHeight']
    slope = prop['foundation'].get('localSlope')
    if slope:
        outer = [(-128,-96),(128,-96),(128,96),(-128,96)]
        inner = [(-96,-64),(96,-64),(96,64),(-96,64)]
        for i,a in enumerate(outer):
            b,c,d = outer[(i+1)%4],inner[(i+1)%4],inner[i]
            author.panel(panels,[(*a,-4),(*b,-4),(*c,12),(*d,12)],palette['stone'])
            author.panel(panels,[(*a,bottom),(*b,bottom),(*b,-4),(*a,-4)],palette['stone'])
            author.panel(panels,[(*c,bottom),(*d,bottom),(*d,12),(*c,12)],palette['stone'])
    else:
        for bounds in [[-128,-96,bottom,128,-64,12],[-128,64,bottom,128,96,12],
                       [-128,-64,bottom,-96,64,12],[96,-64,bottom,128,64,12]]:
            author.box(panels,bounds,palette['stone'])
    # The opaque backing stays above the highest actual ground sample; this is a closed hatch, not a carved hole.
    author.panel(panels,[(-96,-64,0),(96,-64,0),(96,64,0),(-96,64,0)],palette['dark'])
    for x in [-80,-48,-16,16,48,80]:
        author.box(panels,[x-4,-64,4,x+4,64,12],palette['metal'])
    for y in [-36,28]:
        author.box(panels,[-96,y,12,96,y+8,16],palette['metal'])
    # Small end hinges explain a removable service grille without suggesting a usable stairwell yet.
    for x in [-64,48]:
        author.box(panels,[x,58,12,x+16,80,20],palette['metal'])
    if slope:
        for i in range(first,len(panels)):
            points,key,uv = panels[i]
            panels[i] = ([(x,y,z+slope[0]*x+slope[1]*y) for x,y,z in points],key,uv)
