"""Independent rough cloth shelters and inert supplies around a native fire, with no population."""
import math

from author_camps import beam
from author_props import ground_at
from prepare_barbarian_camp import local_world


def fabric_surface(author,panels,grid,key,offset):
    """A joined thin fabric shell with closed outer hems and no doubled internal caps."""
    back=[[tuple(p[i]+offset[i] for i in range(3)) for p in row] for row in grid]
    rows,columns=len(grid),len(grid[0])
    for r in range(rows-1):
        for c in range(columns-1):
            for indices in [[(r,c),(r,c+1),(r+1,c+1)],[(r,c),(r+1,c+1),(r+1,c)]]:
                author.panel(panels,[grid[y][x] for y,x in indices],key)
                author.panel(panels,[back[y][x] for y,x in reversed(indices)],key)
    boundary=[(0,c) for c in range(columns)]+[(r,columns-1) for r in range(1,rows)]
    boundary += [(rows-1,c) for c in range(columns-2,-1,-1)]+[(r,0) for r in range(rows-2,0,-1)]
    for (r,c),(rr,cc) in zip(boundary,boundary[1:]+boundary[:1]):
        author.panel(panels,[grid[r][c],grid[rr][cc],back[rr][cc],back[r][c]],key)


def author_camp(author,prop,palette,height):
    panels=[]
    prop['supportFeet']=[]
    for shelter in prop['shelters']:
        width,depth,top=shelter['width'],shelter['depth'],shelter['top']
        angle=shelter['angle'];cx,cy=shelter['center'];base=shelter['baseZ']
        def point(x,y,z):return (cx+x*math.cos(angle)-y*math.sin(angle),
                                 cy+x*math.sin(angle)+y*math.cos(angle),base+z)
        def roof(y):return top-64*(y+depth/2)/depth
        # Open front looks toward the central fire; uneven rear covers suggest temporary occupation.
        for x in [-width/2+16,width/2-16]:
            for y in [-depth/2+16,depth/2-16]:
                p=point(x,y,0)
                bottom=ground_at(height,local_world(prop,p))-prop['padHeight']-12
                prop['supportFeet'].append(len(panels))
                beam(author,panels,(*p[:2],bottom),point(x,y,roof(y)-8),16,palette['wood'])
            beam(author,panels,point(x,-depth/2,top-8),point(x,depth/2,top-72),16,palette['wood'])
        # Fabric sags between the two side beams. Shared vertices keep its folds watertight.
        cover=[[point(width*(u-.5),depth*(v-.5),roof(depth*(v-.5))-28*math.sin(math.pi*u))
                for u in [0,.25,.5,.75,1]] for v in [0,.5,1]]
        fabric_surface(author,panels,cover,palette['cloth'],(0,0,-3))
        # Rear and partial side curtains have shallow pleats and a free hem above the local ground.
        for side in ['rear','side']:
            grid=[]
            for v in [0,.5,1]:
                row=[]
                for i in range(9):
                    u=i/8
                    fold=12*math.sin(4*math.pi*u)*(1-v)
                    x=width*(u-.5) if side=='rear' else -width/2+fold
                    y=depth/2-fold if side=='rear' else depth*(-.1+.6*u)
                    p=point(x,y,0)
                    bottom=ground_at(height,local_world(prop,p))-prop['padHeight']-base+8+4*(i%2)
                    upper=roof(y)-(28*math.sin(math.pi*u) if side=='rear' else 0)
                    row.append(point(x,y,bottom+(upper-bottom)*v))
                grid.append(row)
            shift=point(0,-3,0) if side=='rear' else point(3,0,0)
            origin=point(0,0,0)
            fabric_surface(author,panels,grid,palette['cloth'],tuple(shift[i]-origin[i] for i in range(3)))
        # Thin bedding follows the ground; a separate rolled end makes its soft purpose readable.
        blanket=[]
        for y in [-16,32,80]:
            row=[]
            for x in [-80,0,80]:
                p=point(x,y,0)
                z=ground_at(height,local_world(prop,p))-prop['padHeight']+4+(3 if x==0 else 0)
                row.append((*p[:2],z))
            blanket.append(row)
        fabric_surface(author,panels,blanket,palette['cloth'],(0,0,-3))
        rings=[]
        for x in [-80,80]:
            ring=[]
            for i in range(8):
                a=math.tau*i/8
                p=point(x,88+16*math.cos(a),0)
                z=ground_at(height,local_world(prop,p))-prop['padHeight']+18+16*math.sin(a)
                ring.append((*p[:2],z))
            rings.append(ring)
        author.panel(panels,list(reversed(rings[0])),palette['cloth'])
        author.panel(panels,rings[1],palette['cloth'])
        for i in range(8):
            j=(i+1)%8
            # Terrain can twist a long roll slightly, so preserve planar native faces with triangles.
            for points in [[rings[0][i],rings[1][i],rings[1][j]],
                           [rings[0][i],rings[1][j],rings[0][j]]]:
                author.panel(panels,points,palette['cloth'])
    # Supplies stay behind the fire approach, between the two unequal shelters.
    for x,y,size in [(-176,528,96),(-72,560,64)]:
        corners=[[x+dx,y+dy] for dx in [0,size] for dy in [0,size]]
        base=min(ground_at(height,local_world(prop,p)) for p in corners)-prop['padHeight']-4
        first=len(panels)
        author.box(panels,[x,y,base,x+size,y+size,base+size],palette['crate'])
        for index in range(first,len(panels)):
            points,key,_=panels[index];panels[index]=(points,key,[(0,0),(1,0),(1,1),(0,1)])
    # A simple empty equipment rack adds a camp-use silhouette without inventing loot or actors.
    for x in [96,288]:
        base=ground_at(height,local_world(prop,[x,640]))-prop['padHeight']-12
        prop['supportFeet'].append(len(panels))
        beam(author,panels,(x,640,base),(x,640,base+256),16,palette['wood'])
    beam(author,panels,(80,640,208),(304,640,208),16,palette['wood'])
    for x in [144,240]:beam(author,panels,(x,624,208),(x,608,208),12,palette['wood'])
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
