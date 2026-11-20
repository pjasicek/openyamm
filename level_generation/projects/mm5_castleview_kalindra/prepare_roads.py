"""Resolve the designed street graph onto native terrain cells before final frontages.

Keep source control points and bounded deviations in the report. A connected raster
is an intermediate source check; painted joins and player access still require review.
"""
import heapq
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent
OUT = PROJECT / 'implementation'
REVIEW = PROJECT / 'review/roads_v1'


def xy(cell):
    r, c = cell
    return ((c - 64) * 512 + 256, (64 - r) * 512 - 256)


def distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / (dx*dx + dy*dy)))
    return math.dist(point, (a[0] + t*dx, a[1] + t*dy))


def corners(building):
    ox, oy = building['frontOrigin']
    tx, ty = building['frontTangent']
    nx, ny = building['frontOutward']
    w, d = building['localFootprint']
    return [(ox+tx*x-nx*y, oy+ty*x-ny*y) for x,y in [(-w/2,0),(w/2,0),(w/2,d),(-w/2,d)]]


def main():
    plan = json.loads((PROJECT / 'layout.json').read_text())
    spec = json.loads((OUT / 'architecture.json').read_text())
    surface = np.array(Image.open(PROJECT / 'landscape/surface_classes.png'))
    heights = np.frombuffer((PROJECT / 'landscape/heightmap.raw').read_bytes(), dtype=np.uint8).reshape(128,128)
    buildings = [b for b in spec['buildings'] if b['form'] not in
                 ['sanctuary','natural_shelter','descent_rim','rope_anchor','canvas_camp','caravan_yard']]
    blocked = set()
    for r in range(127):
        for c in range(127):
            x, y = xy((r,c))
            for b in buildings:
                dx, dy = x-b['frontOrigin'][0], y-b['frontOrigin'][1]
                local_x = dx*b['frontTangent'][0] + dy*b['frontTangent'][1]
                local_y = -dx*b['frontOutward'][0] - dy*b['frontOutward'][1]
                w, d = b['localFootprint']
                if abs(local_x) < w/2+128 and -128 < local_y < d+128:
                    blocked.add((r,c))
                    break
            if surface[r,c] in (0,3,4,7):
                blocked.add((r,c))
    valid = {(r,c) for r in range(127) for c in range(127)} - blocked
    roads, paths, adjustments, snapped = set(), [], [], {}

    def snap(point):
        key = tuple(point)
        if key not in snapped:
            target = min(valid, key=lambda rc: (math.dist(xy(rc), point),rc))
            error = math.dist(xy(target),point)
            assert error <= 1024, ('Control point needs a design correction', point, error)
            snapped[key] = target
            adjustments.append({'original':point, 'cell':target, 'center':xy(target), 'distance':round(error,2)})
        return snapped[key]

    for road in plan['roads']:
        points = [list(p) for p in road['points']]
        # The sketch ended at landmark centers. Stop at their public frontages.
        for index, owner in [(0,'western')] if road['id']=='trade_road' else \
                            ([(len(points)-1,'kalindra')] if road['id']=='castle_approach' else []):
            b = next(b for b in buildings if b['id']==owner)
            point = [b['frontOrigin'][i]+b['frontOutward'][i]*512 for i in range(2)]
            adjustments.append({'road':road['id'], 'original':points[index], 'revised':point,
                                'reason':'Stop at the entrance approach instead of inside the landmark footprint'})
            points[index] = point
        complete = []
        for a,b in zip(points,points[1:]):
            start, end = snap(a), snap(b)
            queue = [(0.,start)]
            costs, previous = {start:0.}, {}
            while queue:
                _, current = heapq.heappop(queue)
                if current==end:
                    break
                for dr,dc in [(-1,0),(0,1),(1,0),(0,-1)]:
                    target = current[0]+dr,current[1]+dc
                    if target not in valid:
                        continue
                    deviation = distance(xy(target),a,b)
                    if deviation > 1024:
                        continue
                    step = (0.85 if target in roads else 1.) + (deviation/512)**2*.4
                    step += abs(int(heights[target])-int(heights[current]))*.015
                    cost = costs[current]+step
                    if cost < costs.get(target,math.inf):
                        costs[target],previous[target] = cost,current
                        heuristic = .85*(abs(target[0]-end[0])+abs(target[1]-end[1]))
                        heapq.heappush(queue,(cost+heuristic,target))
            assert end in costs, ('No road within the bounded source corridor',road['id'],a,b)
            path = [end]
            while path[-1]!=start:
                path.append(previous[path[-1]])
            path.reverse()
            complete.extend(path if not complete else path[1:])
            roads.update(path)
        paths.append({'id':road['id'],'purpose':road['purpose'],'plannedWidth':road['width'],
                      'controlPoints':points,'cells':complete})
    connections={cell:set() for cell in roads}
    for path in paths:
        for a,b in zip(path['cells'],path['cells'][1:]):
            if a==b:
                continue
            assert abs(a[0]-b[0])+abs(a[1]-b[1])==1,(a,b)
            connections[a].add(b);connections[b].add(a)
    reached, pending = set(), [next(iter(roads))]
    while pending:
        cell = pending.pop()
        if cell in reached:
            continue
        reached.add(cell)
        pending.extend(connections[cell]-reached)
    assert reached == roads, 'Road graph disconnected by snapping'
    frontage = []
    for building in buildings:
        if building['district']!='Castleview':
            continue
        for venue in building['venues']:
            if venue.get('heightAbovePad',0):continue
            rc = min(roads,key=lambda cell:math.dist(venue['door'],xy(cell)))
            delta = [xy(rc)[i]-venue['door'][i] for i in range(2)]
            frontage.append({'venue':venue['id'],'door':venue['door'],'nearestRoadCell':rc,
                             'distanceToCenter':round(math.dist(venue['door'],xy(rc)),1),
                             'outwardDistance':round(sum(delta[i]*building['frontOutward'][i] for i in range(2)),1),
                             'lateralError':round(sum(delta[i]*building['frontTangent'][i] for i in range(2)),1)})
    result = {'status':'connected native road source; painted road/frontage acceptance pending',
              'paths':paths,'cells':sorted(roads),'adjustments':adjustments,'frontages':frontage,
              'checks':{'connected':True,'roadCells':len(roads),'blockedCellCrossings':len(roads&blocked)},
              'limits':'One-cell orthogonal raster; diagonal pairs, road artwork, gates and frontage fit await review.'}
    (OUT/'roads.json').write_text(json.dumps(result,indent=2)+'\n')
    REVIEW.mkdir(parents=True,exist_ok=True)
    for name,limits in [('town',(-9800,4200,-8600,9000)),('region',(-24576,24576,-24576,24576))]:
        fig,ax=plt.subplots(figsize=(12,12))
        ax.imshow(surface,extent=(-32768,32768,-32768,32768),cmap='terrain',alpha=.25,origin='upper')
        for road in plan['roads']:
            ax.plot(*zip(*road['points']),color='#c55d27',linestyle='--',linewidth=1)
        for path in paths:
            ax.plot(*zip(*(xy(rc) for rc in path['cells'])),color='#4f3c29',linewidth=2)
        for building in buildings:
            ax.add_patch(Polygon(corners(building),facecolor='#b7afa1',edgecolor='#403e3c',linewidth=.7))
            x,y=building['center']
            if limits[0]<x<limits[1] and limits[2]<y<limits[3]:
                ax.text(x,y,building['id'],fontsize=7,ha='center')
            for venue in building['venues']:
                if venue.get('heightAbovePad',0):continue
                x,y=venue['door'];nx,ny=building['frontOutward']
                ax.arrow(x,y,nx*256,ny*256,width=18,color='#167697')
        ax.plot(*zip(*(spec['fortifications']['polygon']+[spec['fortifications']['polygon'][0]])),color='#665171')
        for gate in spec['gates']:
            ax.scatter(*gate['point'],s=75,facecolors='white',edgecolors='#665171',zorder=8)
        ax.set(xlim=limits[:2],ylim=limits[2:],aspect='equal',title='Native road source: dashed design / solid cell centers')
        fig.tight_layout();fig.savefig(REVIEW/(name+'.png'),dpi=150);plt.close(fig)
    print(json.dumps(result['checks']))


if __name__=='__main__':
    main()
