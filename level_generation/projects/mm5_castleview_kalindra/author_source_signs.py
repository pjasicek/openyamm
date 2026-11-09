"""Original timber boards with a slightly leaning post, rear brace and readable front."""
from author_camps import beam


def author_sign(author,prop,palette):
    panels = []
    bottom = prop['foundation']['postBottomZ']-prop['padHeight']
    post = []
    author.box(post,[-14,10,bottom,14,38,316],palette['wood'])
    for points,key,uv in post:
        panels.append(([(x+12*(z-bottom)/(316-bottom),y,z) for x,y,z in points],key,uv))
    author.box(panels,[-136,-16,156,136,8,292],palette['wood'])
    beam(author,panels,(-96,24,184),(96,24,256),16,palette['wood'])
    author.panel(panels,[(-128,-17,160),(128,-17,160),(128,-17,288),(-128,-17,288)],
                 prop['faceTexture'],[(0,0),(1,0),(1,1),(0,1)])
    for x,z in [(-120,282),(120,166)]:
        author.box(panels,[x-2,-19,z-2,x+2,-17,z+2],palette['metal'])
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
