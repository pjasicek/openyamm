"""Original timber crossings with native-terrain-fitted masonry bank landings."""
import math

from author_props import ground_at
from review_environment import edge_samples


def author_bridge(author, bridge, palette, height):
    width,length=bridge['width'],bridge['length']
    deck=bridge['padHeight']
    bridge['geometryChecks']=[]
    author.material(palette['wood'])
    texture_width,texture_height=author.sizes[palette['wood']]

    def checked_box(panels,bounds,key,kind,omit_faces=()):
        face=len(panels)+4-sum(i<4 for i in omit_faces)
        author.box(panels,bounds,key,omit_faces=omit_faces)
        bridge['geometryChecks'].append({'model':model_name,'faces':[face],
                                        'kind':kind,'sourceBounds':bounds})

    def world(x,y):
        return [bridge['frontOrigin'][i]+bridge['frontTangent'][i]*x-bridge['frontOutward'][i]*y
                for i in range(2)]

    def local(point):
        delta=[point[i]-bridge['frontOrigin'][i] for i in range(2)]
        return (sum(delta[i]*bridge['frontTangent'][i] for i in range(2)),
                -sum(delta[i]*bridge['frontOutward'][i] for i in range(2)),point[2]-deck)

    def footing_bottom(bounds):
        x0,y0,x1,y1=bounds
        poly=[world(x,y) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
        samples=[ground_at(height,p) for a,b in zip(poly,poly[1:]+poly[:1]) for p in edge_samples(a,b)]
        return math.floor(min(samples)-deck)-32

    bays=math.ceil(length/512)
    for index in range(bays):
        first,last=index*length/bays,(index+1)*length/bays
        panels=[]
        model_name=bridge['id']+'_bay_'+str(index).zfill(2)
        # Adjacent bays meet exactly. Keep outer end caps and remove only their paired internal y faces.
        joint_caps=tuple(face for face,internal in [(0,index>0),(2,index<bays-1)] if internal)
        # Continuous planked floor: no physical gaps that can catch the party.
        author.box(panels,[-width/2,first,-32,width/2,last,0],palette['wood'],omit_faces=joint_caps)
        points,key,_=panels[-1]
        panels[-1]=(points,key,[(x/texture_width,y/texture_height) for x,y,z in points])
        bridge['geometryChecks'].append({'model':model_name,'faces':[len(panels)-1],'kind':'walking surface'})
        for side in [-1,1]:
            x=side*(width/2-48)
            checked_box(panels,[x-20,first,-64,x+20,last,-32],palette['wood'],'clear beam underside',joint_caps)
            rail_x=side*(width/2-16)
            for z in [64,128]:
                author.box(panels,[rail_x-8,first,z,rail_x+8,last,z+16],palette['wood'],omit_faces=joint_caps)
            for y in ([first+16,last-16] if index==bays-1 else [first+16]):
                author.box(panels,[rail_x-16,y-12,0,rail_x+16,y+12,144],palette['wood'])
            pile_y=(first+last)/2
            bounds=[x-24,pile_y-24,x+24,pile_y+24]
            bottom=footing_bottom(bounds)
            checked_box(panels,[bounds[0],bounds[1],bottom,bounds[2],bounds[3],-64],palette['wood'],'buried pile foot')
        checked_box(panels,[-width/2+32,pile_y-20,-80,width/2-32,pile_y+20,-64],palette['wood'],
                    'clear beam underside')
        author.model(model_name,panels,bridge)

    for surface in bridge['surfaces']:
        if surface['id']=='deck':
            continue
        panels=[]
        model_name=bridge['id']+'_'+surface['id']
        corners=[local(p) for p in surface['corners']]
        first,last=surface['localY']
        bottom=footing_bottom([-width/2,first,width/2,last])
        lower=[(x,y,bottom) for x,y,z in corners]
        # Native triangles explicitly match the checked walking-surface diagonal.
        for ids in [(0,1,2),(0,2,3)]:
            author.panel(panels,[corners[i] for i in ids],palette['wood'],
                         [(corners[i][0]/texture_width,corners[i][1]/texture_height) for i in ids])
        author.panel(panels,list(reversed(lower)),palette['stone'])
        bridge['geometryChecks'].append({'model':model_name,'faces':[0,1],'kind':'walking surface'})
        bridge['geometryChecks'].append({'model':model_name,'faces':[2],'kind':'buried abutment foot'})
        for i in range(4):
            j=(i+1)%4
            author.panel(panels,[lower[i],lower[j],corners[j],corners[i]],palette['stone'])
        # Side rails follow each ramp edge's individual slope. The full bank edge
        # stays open, including where native ground differs across the deck width.
        for a,b in [(corners[0],corners[3]),(corners[1],corners[2])]:
            center=a[0]+(16 if a[0]<0 else -16)
            for z in [64,128]:
                ring=[(center-8,a[1],a[2]+z),(center-8,b[1],b[2]+z),
                      (center-8,b[1],b[2]+z+16),(center-8,a[1],a[2]+z+16)]
                other=[(x+16,y,h) for x,y,h in ring]
                author.panel(panels,list(reversed(ring)),palette['wood'])
                author.panel(panels,other,palette['wood'])
                for i in range(4):
                    j=(i+1)%4
                    author.panel(panels,[ring[i],ring[j],other[j],other[i]],palette['wood'])
            bank=a if surface['id']=='start_ramp' else b
            y=bank[1]+(16 if surface['id']=='start_ramp' else -16)
            t=(y-a[1])/(b[1]-a[1])
            top=a[2]+t*(b[2]-a[2])
            bounds=[center-16,y-12,center+16,y+12]
            checked_box(panels,[bounds[0],bounds[1],footing_bottom(bounds),bounds[2],bounds[3],top+144],
                        palette['wood'],'buried rail foot')
        author.model(model_name,panels,bridge)
    author.semantic.setdefault('bridges',[]).append(bridge)
