"""Small source-inspired Monga Melon groups with striped fruit and low purple vines."""
import math

from author_props import ground_at


def ground_stem(author, panels, first, last, width, key):
    # Two raised upper surfaces retain the narrow stem from either side; no hidden bottom or end caps.
    dx, dy = last[0]-first[0], last[1]-first[1]
    length = math.hypot(dx, dy)
    offset = [-dy/length*width/2, dx/length*width/2, 0]
    ridge = [[p[0], p[1], p[2]+width/2] for p in [first, last]]
    left = [[p[i]+offset[i] for i in range(3)] for p in [first, last]]
    right = [[p[i]-offset[i] for i in range(3)] for p in [first, last]]
    author.panel(panels, [right[0], right[1], ridge[1], ridge[0]], key)
    author.panel(panels, [ridge[0], ridge[1], left[1], left[0]], key)


def fruit_geometry(radii,angle):
    rx,ry,rz = radii
    def vertex(phi,theta):
        x,y = rx*math.cos(phi)*math.cos(theta),ry*math.cos(phi)*math.sin(theta)
        return [round(x*math.cos(angle)-y*math.sin(angle)),
                round(x*math.sin(angle)+y*math.cos(angle)),round(rz*(1+math.sin(phi)))]
    rings = [[vertex(phi,i*math.tau/8) for i in range(8)]
             for phi in [-math.pi/3,-math.pi/6,0,math.pi/6,math.pi/3]]
    panels = []
    for j in range(4):
        for i in range(8):
            k = (i+1)%8
            panels.append(([rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]],
                           [(i/8,(j+1)/6),((i+1)/8,(j+1)/6),((i+1)/8,(j+2)/6),(i/8,(j+2)/6)]))
    for i in range(8):
        k = (i+1)%8
        panels.append(([rings[0][k],rings[0][i],[0,0,0]],[( (i+1)/8,1/6),(i/8,1/6),(i/8,0)]))
        panels.append(([rings[-1][i],rings[-1][k],[0,0,2*rz]],[(i/8,5/6),((i+1)/8,5/6),(i/8,1)]))
    return panels


def author_patch(author,prop,palette,height):
    panels = []
    prop['fruitFaceRanges'] = []
    for fruit in prop['fruit']:
        first_face = len(panels)
        for points,uv in fruit_geometry(fruit['radii'],fruit['angle']):
            author.panel(panels,[[v[i]+fruit['center'][i] for i in range(3)] for v in points],palette['fruit'],uv)
        prop['fruitFaceRanges'].append([first_face,len(panels)])
    # The compact stems and leaves hug the native grade at their own positions; fruit are rigid fitted solids.
    def terrain_point(x,y,lift):
        world = [prop['frontOrigin'][0]+x,prop['frontOrigin'][1]+y]
        return [x,y,ground_at(height,world)-prop['padHeight']+lift]
    for first,middle,last in prop['vines']:
        points = [terrain_point(*p,4) for p in [first,middle,last]]
        ground_stem(author,panels,points[0],points[1],5,palette['stem'])
        ground_stem(author,panels,points[1],points[2],5,palette['stem'])
    for first,last in prop['leafStalks']:
        ground_stem(author,panels,terrain_point(*first,3),terrain_point(*last,3),3,palette['stem'])
    outline = [(0,-28),(10,-18),(22,0),(14,18),(0,36),(-14,18),(-22,0),(-10,-18)]
    for leaf in prop['leaves']:
        x,y,angle,scale = leaf
        points = [terrain_point(x+(u*math.cos(angle)-v*math.sin(angle))*scale,
                                y+(u*math.sin(angle)+v*math.cos(angle))*scale,3) for u,v in outline]
        center = terrain_point(x,y,9)
        for i in range(8):
            j = (i+1)%8
            author.panel(panels,[points[i],points[j],center],palette['leaf'],
                         [(outline[i][0]/44+.5,(outline[i][1]+28)/64),
                          (outline[j][0]/44+.5,(outline[j][1]+28)/64),(.5,28/64)])
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
