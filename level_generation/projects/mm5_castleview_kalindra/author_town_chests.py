"""Original small timber chests with curved lids, iron straps, hinges and a front hasp."""
import math


def geometry(author,panels,prop,palette):
    bottom = prop['foundation']['feetBottomZ']-prop['padHeight']
    # Four short feet take up the small grade difference without floating a whole bottom face.
    for x in [-88,64]:
        for y in [-48,24]:
            author.box(panels,[x,y,bottom,x+24,y+24,16],palette['wood'],omit_faces=(5,))
    author.box(panels,[-96,-56,12,96,56,76],palette['wood'],omit_faces=(5,))
    author.box(panels,[-96,-56,76,96,56,80],palette['dark'],omit_faces=(4,5))
    profile = [(round(56*math.cos(i*math.pi/8)),80+round(48*math.sin(i*math.pi/8))) for i in range(9)]
    width,height = author.sizes[palette['wood']]
    arc = 0
    for (y0,z0),(y1,z1) in zip(profile,profile[1:]):
        end = arc+math.hypot(y1-y0,z1-z0)
        author.panel(panels,[(-96,y0,z0),(-96,y1,z1),(96,y1,z1),(96,y0,z0)],palette['wood'],
                     [(-96/width,arc/height),(-96/width,end/height),(96/width,end/height),(96/width,arc/height)])
        arc = end
    author.panel(panels,[(-96,y,z) for y,z in reversed(profile)],palette['wood'])
    author.panel(panels,[(96,y,z) for y,z in profile],palette['wood'])
    # Raised narrow iron straps follow the curved lid and continue down the timber box.
    for x in [-64,52]:
        for (y0,z0),(y1,z1) in zip(profile,profile[1:]):
            author.panel(panels,[(x,y0,z0+2),(x,y1,z1+2),(x+12,y1,z1+2),(x+12,y0,z0+2)],palette['metal'])
        for y in [-58,56]:
            author.box(panels,[x,y,12,x+12,y+2,80],palette['metal'],
                       omit_faces=(2,) if y<0 else (0,))
    author.box(panels,[-14,-62,48,14,-56,92],palette['metal'])
    author.box(panels,[-3,-64,59,3,-62,69],palette['dark'],omit_faces=(1,2,3,4,5))
    for x in [-64,48]:
        author.box(panels,[x,56,66,x+16,62,94],palette['metal'])


def author_chest(author,prop,palette):
    panels = []
    geometry(author,panels,prop,palette)
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
