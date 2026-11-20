"""Original low-sided green message bottles resting on their sides, with visible rolled paper."""
import math


def geometry():
    panels = []
    tilt = math.pi/2

    def ring(radius,z):
        return [(radius*math.cos(i*math.tau/8),radius*math.sin(i*math.tau/8),z) for i in range(8)]

    def band(first,last,key):
        for i in range(8):
            j = (i+1)%8
            panels.append(([first[i],first[j],last[j],last[i]],key,
                           [(i/8,0),( (i+1)/8,0),((i+1)/8,1),(i/8,1)]))

    profile = [(14,0),(22,6),(22,64),(12,78),(12,106),(16,108),(16,114)]
    for a,b in zip(profile,profile[1:]): band(ring(*a),ring(*b),'glass')
    panels.append((list(reversed(ring(*profile[0]))),'glass',None))
    band(ring(16,114),ring(9,114),'glass')
    # Paper protrudes through the open lip, with a modeled hollow roll instead of a solid white rod.
    band(ring(8,104),ring(8,146),'paper')
    band(ring(8,146),ring(4,146),'paper')
    # Keep the octagonal open roll, closing its hidden interior with a recessed tapered end.
    opening = ring(4,146)
    for i in range(8):
        j = (i+1)%8
        panels.append(([opening[j],opening[i],(0,0,114)],'paper',None))
    result = []
    for points,key,uv in panels:
        transformed = [(round(x*math.cos(tilt)+z*math.sin(tilt)-52),round(y),
                        round(-x*math.sin(tilt)+z*math.cos(tilt))) for x,y,z in points]
        result.append((transformed,key,uv))
    return result


def author_bottle(author,prop,palette):
    panels = []
    for points,key,uv in geometry():
        author.panel(panels,points,palette[key],uv)
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
