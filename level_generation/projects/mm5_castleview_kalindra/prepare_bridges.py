"""Resolve both reserved bridge decks and bank ramps against native terrain triangles.

This writes a geometry specification, not a claim of authored or traversable bridges.
"""
import hashlib
import json
import math
from pathlib import Path

from author_props import ground_at
from review_environment import edge_samples

PROJECT=Path(__file__).resolve().parent


def triangle_clearance(height, triangle):
    a,b,c=triangle
    determinant=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

    def barycentric(point):
        px,py=point[0]-a[0],point[1]-a[1]
        u=(px*(c[1]-a[1])-py*(c[0]-a[0]))/determinant
        v=((b[0]-a[0])*py-(b[1]-a[1])*px)/determinant
        return u,v

    candidates=[point for first,last in zip(triangle,triangle[1:]+triangle[:1])
                for point in edge_samples(first,last)]
    for x in range(math.ceil(min(p[0] for p in triangle)/512),
                   math.floor(max(p[0] for p in triangle)/512)+1):
        for y in range(math.ceil(min(p[1] for p in triangle)/512),
                       math.floor(max(p[1] for p in triangle)/512)+1):
            u,v=barycentric([x*512,y*512])
            if u>=-1e-8 and v>=-1e-8 and u+v<=1+1e-8:
                candidates.append([x*512,y*512])
    samples=[]
    for point in candidates:
        u,v=barycentric(point)
        top=a[2]+u*(b[2]-a[2])+v*(c[2]-a[2])
        samples.append({'point':point,'surfaceZ':top,'groundZ':ground_at(height,point),
                        'clearance':top-ground_at(height,point)})
    return {'minimum':min(s['clearance'] for s in samples),
            'maximum':max(s['clearance'] for s in samples),'samples':samples}


def prepare():
    height=(PROJECT/'landscape/heightmap.raw').read_bytes()
    spec=json.loads((PROJECT/'implementation/architecture.json').read_text())
    output=[]
    for source in spec['bridges']:
        axis=0 if source['extent'][0]>source['extent'][1] else 1
        length=source['extent'][axis]
        width=source['extent'][1-axis]
        origin=list(source['point'])
        origin[axis]-=length/2
        tangent=[0,-1] if axis==0 else [1,0]
        outward=[-1,0] if axis==0 else [0,-1]
        deck=source['terrainCheck']['deckTop']

        def world(x,y,z):
            return [origin[i]+tangent[i]*x-outward[i]*y for i in range(2)]+[z]

        sections=[('deck',0,length,None)]
        # Reger's short western ramp ends on the existing flat islet, 32 units
        # before the corrected house doorway. Do not run it through the house.
        start_run=192 if source['id']=='reger_crossing' else 512
        sections += [('start_ramp',-start_run,0,'start'),('end_ramp',length,length+512,'end')]
        surfaces=[]
        for name,first,last,bank in sections:
            corners=[world(-width/2,first,deck),world(width/2,first,deck),
                     world(width/2,last,deck),world(-width/2,last,deck)]
            if bank:
                for index in ([0,1] if bank=='start' else [2,3]):
                    corners[index][2]=ground_at(height,corners[index])
            triangles=[[corners[i] for i in ids] for ids in [(0,1,2),(0,2,3)]]
            checks=[triangle_clearance(height,t) for t in triangles]
            minimum=min(c['minimum'] for c in checks)
            assert minimum>=-1e-6,(source['id'],name,minimum)
            surfaces.append({'id':name,'localY':[first,last],'corners':corners,'triangles':triangles,
                             'minimumGroundClearance':minimum,'checks':checks})
        output.append({'id':source['id'],'title':source['title'],'semanticId':'mm5:sw/'+source['id'],
                       'frontOrigin':origin,'frontTangent':tangent,'frontOutward':outward,'padHeight':deck,
                       'width':width,'length':length,'localFootprint':[width,length],'surfaces':surfaces,
                       'construction':'Original timber deck, supporting beams/piles, rails and fitted bank landings.',
                       'source':source,'geometryStatus':'Specified; meshes and native traversal remain outstanding.'})
    report={'heightmapSha256':hashlib.sha256(height).hexdigest(),'bridges':output,
            'method':'Each proposed surface triangle is checked at its edges split by native grid/diagonal crossings '
                     'and at contained native grid vertices. These cover extrema of the difference between '
                     'piecewise-linear surfaces. Bank edges meet native ground; deck clearance is checked over full width.',
            'limits':'Walking surfaces only. Author and check structural undersides, pile feet, rails and abutments; '
                     'then inspect actual renders and prove ordinary native movement in both directions.'}
    path=PROJECT/'implementation/bridge_layout.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print({b['id']:{s['id']:round(s['minimumGroundClearance'],3) for s in b['surfaces']} for b in output})


if __name__=='__main__':
    prepare()
