"""Modest original signs for the three mapmakers and the shared tailor/cobbler frontage."""

PALETTE = {'jethro':'mm5jethro','lydia':'mm5lydia','miles':'mm5miles',
           'tailor':'mm5tailor','cobbler':'mm5cobble'}


def configure(building):
    signs = []
    if building['id']=='maps':
        for venue,key in zip(building['venues'],['jethro','lydia','miles']):
            x = venue['localOffset']
            signs.append({'id':key,'venueId':venue['id'],'label':venue['displayLabel'],
                          'mount':'facade','bounds':[x-72,-12,272,x+72,2,352],
                          'artBounds':[x-64,-13,280,x+64,-13,344],'texture':PALETTE[key]})
    if building['id']=='crafts':
        for venue,key,x,y in zip(building['venues'],['tailor','cobbler'],[-420,320],[-164,-132]):
            signs.append({'id':key,'venueId':venue['id'],'label':venue['displayLabel'],
                          'mount':'canopy','bounds':[x-72,y,104,x+72,y+12,248],
                          'artBounds':[x-64,y-1,112,x+64,y-1,240],'texture':PALETTE[key],
                          'hangers':[[x-46,y+4,248,x-40,y+10,264],
                                     [x+40,y+4,248,x+46,y+10,264]]})
    if signs:
        building['exteriorSigns'] = signs
        building['implementationNotes'].append(
            'Original small frontage signs identify existing venues; signs are inert and doors retain their handlers.')


def author_signs(author,panels,building,palette):
    for sign in building.get('exteriorSigns',[]):
        author.box(panels,sign['bounds'],palette['wood'])
        for support in sign.get('hangers',[]):
            author.box(panels,support,palette['metal'])
        x0,y,z0,x1,_,z1 = sign['artBounds']
        author.panel(panels,[(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)],sign['texture'],
                     [(0,0),(1,0),(1,1),(0,1)])
