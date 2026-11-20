"""Native roads, original terrain banks and authored dark-dirt/sand transitions."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

from terrain_materials import acid_name

PROJECT = Path(__file__).resolve().parent
VARIANTS = {0:0,1:22,2:20,4:23,8:21,3:18,5:17,10:16,12:19,7:14,11:12,13:15,14:13}
ROAD_VARIANTS = {15:0,5:1,10:2,3:3,9:4,6:5,12:6,7:7,13:8,11:9,14:10,1:13,2:14,4:11,8:12}
DIAGONAL_VARIANTS = {3:20,12:19,6:21,9:22}


def assign(palette, indexed, *, project=PROJECT):
    classes = np.array(Image.open(project/'landscape/surface_classes.png'))
    heights = np.frombuffer((project/'landscape/heightmap.raw').read_bytes(),dtype=np.uint8).reshape(128,128)
    plan = json.loads((project/'implementation/roads.json').read_text())
    roads = {tuple(cell) for cell in plan['cells']}
    edges = {frozenset([tuple(a),tuple(b)]) for path in plan['paths']
             for a,b in zip(path['cells'],path['cells'][1:]) if a!=b}
    # Only retain a non-dirt vertex when its surrounding source cells agree.
    # Each supported material gets a dirt collar; shore quads remain entirely
    # within originally flat fluid cells, preserving the authored water planes.
    padded = np.pad(classes,((1,0),(1,0)),mode='edge')
    fields = [padded[dr:dr+128,dc:dc+128] for dr,dc in [(0,0),(0,1),(1,0),(1,1)]]
    nodes = np.where(np.logical_and.reduce([f==fields[0] for f in fields]),fields[0],2).astype(np.uint8)
    spec = json.loads((project/'implementation/architecture.json').read_text())
    rows,columns=np.indices((128,128));x=(columns-64)*512;y=(64-rows)*512
    for building in spec['buildings']:
        if building['district']!='Castleview':
            continue
        cx,cy=building['center'];w,d=building['reservedEnvelope']
        nodes[(abs(x-cx)<=w/2+128)&(abs(y-cy)<=d/2+128)]=2
    for r,c in roads:
        nodes[r:r+2,c:c+2]=2
    removed=[]
    while True:
        changes=0
        for r in range(127):
            for c in range(127):
                block=nodes[r:r+2,c:c+2]
                for family in [1,3,4,5,8,10]:
                    bits=sum(int(block[dr,dc]!=family)<<i for i,(dr,dc) in enumerate([(0,0),(0,1),(1,0),(1,1)]))
                    if bits in (6,9):
                        positions=np.argwhere(block==family)
                        dr,dc=positions[-1]
                        nodes[r+dr,c+dc]=2
                        removed.append([int(r+dr),int(c+dc),family]);changes+=1
        if not changes:
            break
    materials={0:'mm5void',1:'grastyl',2:'dirttyl',3:'wtrtyl',4:'mm5acid',5:'7sand',8:'voltyl',10:'rctyl'}
    tiles=np.array([palette[materials[int(c)]] for c in classes.flat],dtype=np.uint8).reshape(128,128)
    family_banks={1:90,3:126,4:126,8:198,10:306}
    counts={};unresolved=[];geometry_boundaries=[];water_quads=0
    for r in range(127):
        for c in range(127):
            original=int(classes[r,c]);block=nodes[r:r+2,c:c+2]
            if original==0:
                if np.any(block!=original):
                    target = geometry_boundaries if original == 0 else unresolved
                    target.append({'cell':[r,c],'family':materials[original]})
                continue
            families=set(int(v) for v in block.flat)-{2}
            assert len(families)<=1,('Incompatible native transition',r,c,families)
            if not families:
                name='dirttyl'
            else:
                family=next(iter(families))
                assert family in family_banks or family==5,(r,c,family)
                bits=sum(int(block[dr,dc]!=family)<<i for i,(dr,dc) in enumerate([(0,0),(0,1),(1,0),(1,1)]))
                if family==5:
                    name='7sand' if bits==0 else f'mm5sd{bits:02d}'
                else:
                    name=indexed[family_banks[family]+VARIANTS[bits]][1].lower()
                if family==4:
                    name=acid_name(VARIANTS[bits])
                # The merged table repeats rcw at the SW slot; use the actual
                # native rcsw bitmap, already present in the donor texture set.
                if family==10 and bits==13:
                    name='rcsw'
                if family in (3,4):
                    expected=8 if family==3 else 24
                    assert np.all(heights[r:r+2,c:c+2]==expected),('Non-flat fluid quad',r,c)
                    water_quads+=1
            tiles[r,c]=palette[name];counts[name]=counts.get(name,0)+1
    neighbors = {cell:set() for cell in roads}
    for a,b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    # Connectivity owns ports; physical adjacency alone must not create a junction.
    road_ports = {cell:sum(1<<i for i,(dr,dc) in enumerate([(-1,0),(0,1),(1,0),(0,-1)])
                          if (cell[0]+dr,cell[1]+dc) in neighbors[cell]) for cell in roads}
    diagonal_records = []
    opposite = {3:12,12:3,6:9,9:6}
    for r,c in sorted(roads):
        assert classes[r,c] not in (0,3,4,7),(r,c)
        bits = road_ports[r,c]
        if c==126:
            bits |= 2
        assert bits in ROAD_VARIANTS,(r,c,bits)
        variant = ROAD_VARIANTS[bits]
        paired = sorted(n for n in neighbors[r,c] if road_ports[n]==opposite.get(bits))
        if paired:
            variant = DIAGONAL_VARIANTS[bits]
            diagonal_records.append({'cell':[r,c], 'portsNESW':bits, 'pairedNeighbors':paired,
                                     'texture':indexed[414+variant][1].lower()})
        tiles[r,c]=palette[indexed[414+variant][1].lower()]
    report={'status':'all categorical material joins assigned; regional visual and frontage review remains open',
            'roadCells':len(roads),'flatWaterOrShoreQuads':water_quads,'transitionCounts':counts,
            'diagonalRoadCells':diagonal_records,
            'removedSaddleVertices':removed,'unresolvedBoundaryCells':unresolved,
            'geometryBoundaryCells':geometry_boundaries,
            'geometryBoundaryTreatment':'source-owned cliff/boundary/spill models; see implementation/world_rim.json',
            'limitations':['regional scenery/rim composition and final road grades/frontage fit pending']}
    (project/'implementation/terrain_assignment.json').write_text(json.dumps(report,indent=2)+'\n')
    Image.fromarray(nodes).save(project/'implementation/terrain_corner_classes.png')
    return tiles.tobytes()
