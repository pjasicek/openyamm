"""Original roofed stone wells, with timber windlasses and suspended buckets."""
import math


def geometry(author,panels,prop,palette):
    bottom = prop['foundation']['skirtBottomZ']-prop['padHeight']
    def ring(radius,z):
        return [(round(radius*math.cos(i*math.tau/12)),round(radius*math.sin(i*math.tau/12)),z)
                for i in range(12)]
    def band(r0,z0,r1,z1,key):
        a,b = ring(r0,z0),ring(r1,z1)
        for i in range(12):
            author.panel(panels,[a[i],a[(i+1)%12],b[(i+1)%12],b[i]],palette[key])
    band(128,bottom,128,96,'stone')
    band(136,96,136,112,'stone')
    band(136,112,88,112,'stone')
    band(88,112,88,8,'stone')
    water = ring(88,8)
    author.panel(panels,water,palette['water'],[(x/128,y/128) for x,y,z in water])
    for x in [-128,104]:
        author.box(panels,[x,-16,bottom,x+24,16,328],palette['wood'])
    # Two pitched roof slabs with thickness and closed timber gables.
    for sign in [-1,1]:
        y = sign*144
        top = [(-176,y,320),(-176,0,432),(176,0,432),(176,y,320)]
        if sign==-1:top.reverse()
        author.panel(panels,top,palette['roof'])
        underside = [(x,y,z-12) for x,y,z in reversed(top)]
        author.panel(panels,underside,palette['wood'])
        for a,b in zip(top,top[1:]+top[:1]):
            if a[1]==b[1]==0:continue
            author.panel(panels,[a,(a[0],a[1],a[2]-12),(b[0],b[1],b[2]-12),b],palette['wood'])
    for x in [-140,140]:
        points = [(x,-132,308),(x,132,308),(x,0,412)]
        if x<0:points.reverse()
        author.panel(panels,points,palette['wood'])
    author.box(panels,[-152,-20,300,152,20,324],palette['wood'])
    # Horizontal octagonal windlass, supported by the two posts.
    profile = [(round(18*math.cos(i*math.tau/8)),224+round(18*math.sin(i*math.tau/8))) for i in range(8)]
    for (y0,z0),(y1,z1) in zip(profile,profile[1:]+profile[:1]):
        author.panel(panels,[(-144,y0,z0),(-144,y1,z1),(144,y1,z1),(144,y0,z0)],palette['wood'])
    author.panel(panels,[(-144,y,z) for y,z in reversed(profile)],palette['metal'])
    author.panel(panels,[(144,y,z) for y,z in profile],palette['metal'])
    author.box(panels,[144,-8,176,156,8,228],palette['metal'])
    author.box(panels,[144,-12,168,172,12,188],palette['wood'])
    # Rope and empty open bucket hang inside the ring, without clipping its water plane.
    author.box(panels,[-3,-3,96,3,3,224],palette['wood'])
    outer = [(-24,-24), (24,-24), (24,24), (-24,24)]
    inner = [(-18,-18), (18,-18), (18,18), (-18,18)]
    band_outer = [(-26,-26), (26,-26), (26,26), (-26,26)]
    for i in range(4):
        j = (i+1)%4
        a,b,c,d = outer[i],outer[j],inner[i],inner[j]
        author.panel(panels,[(*a,36),(*b,36),(*b,88),(*a,88)],palette['wood'])
        author.panel(panels,[(*d,42),(*c,42),(*c,88),(*d,88)],palette['wood'])
        author.panel(panels,[(*a,88),(*b,88),(*d,88),(*c,88)],palette['wood'])
        a,b,c,d = band_outer[i],band_outer[j],outer[i],outer[j]
        author.panel(panels,[(*a,74),(*b,74),(*b,82),(*a,82)],palette['metal'])
        author.panel(panels,[(*a,82),(*b,82),(*d,82),(*c,82)],palette['metal'])
        author.panel(panels,[(*c,74),(*d,74),(*b,74),(*a,74)],palette['metal'])
    author.panel(panels,[(*p,36) for p in reversed(outer)],palette['wood'])
    author.panel(panels,[(*p,42) for p in inner],palette['wood'])
    for bounds,omit in [([-22,-3,86,-18,3,104],(4,5)),([18,-3,86,22,3,104],(4,5)),
                        ([-22,-3,100,22,3,104],(1,3))]:
        author.box(panels,bounds,palette['metal'],omit_faces=omit)


def author_well(author,prop,palette):
    panels = []
    geometry(author,panels,prop,palette)
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
