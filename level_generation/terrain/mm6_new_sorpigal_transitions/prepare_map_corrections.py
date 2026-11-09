"""Find the smallest land-tile substitution set resolving native corner conflicts; export a hashed patch."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
records=json.loads((P/'mask_inventory.json').read_text())['masks']
sig={r['tile']:tuple(r['corners_NW_NE_SE_SW']) for r in records}
sig.update({'6dirttyl':('dirt',)*4,'6grastyl':('grass',)*4,'6voltyl':('volcano',)*4})
allowed={sig[n]:n for n in sig if n.startswith('6grdrt') or n in ('6dirttyl','6grastyl')}
rows=list(csv.DictReader((P.parent/'mm6_new_sorpigal/map_cells.csv').open()))
grid={(int(r['column']),int(r['row'])):r['texture'] for r in rows}
vertices=collections.defaultdict(list)
offsets=[(0,0),(1,0),(1,1),(0,1)]
for (x,y),name in grid.items():
 if name in sig:
  for i,(dx,dy) in enumerate(offsets):vertices[x+dx,y+dy].append((sig[name][i],x,y,name))
bad={k:v for k,v in vertices.items() if len({t[0] for t in v})>1}
keys=sorted(bad)
best=None
for bits in itertools.product(['dirt','grass'],repeat=len(keys)):
 assignments=dict(zip(keys,bits));changed={};valid=True
 for (x,y),name in grid.items():
  if name not in sig:continue
  target=tuple(assignments.get((x+dx,y+dy),sig[name][i]) for i,(dx,dy) in enumerate(offsets))
  if target==sig[name]:continue
  if name not in allowed.values() or target not in allowed:valid=False;break
  changed[x,y]=allowed[target]
 if valid and (best is None or (len(changed),str(changed))<(len(best),str(best))):best=changed
assert best is not None
fixed={**grid,**best}
for (x,y),a in fixed.items():
 for dx,dy,aa,bb in [(1,0,(1,2),(0,3)),(0,1,(3,2),(0,1))]:
  b=fixed.get((x+dx,y+dy))
  if a in sig and b in sig:assert tuple(sig[a][i] for i in aa)==tuple(sig[b][i] for i in bb)
catalogue=json.loads((P.parent/'mm6_new_sorpigal/catalogue.json').read_text())
ids={t['name']:t['raw_tile_ids'][0] for t in catalogue['tiles']}
source=ROOT/catalogue['source_map']
sys.path.insert(0,str(ROOT/'util'))
import map_export
native=map_export.parse_odm_file(source)['payload']
data=bytearray(source.read_bytes())
height_offset=map_export.TERRAIN_SECTION_OFFSET_V8 if native['version']==8 else map_export.TERRAIN_SECTION_OFFSET
tile_offset=height_offset+map_export.TERRAIN_MAP_SIZE
changes=[]
for (x,y),name in sorted(best.items()):
 offset=tile_offset+y*128+x
 changes.append({'column':x,'row':y,'world_x':-32768+x*512,'world_y':32768-y*512,
                 'before':grid[x,y],'after':name,'before_raw_id':data[offset],'after_raw_id':ids[name],
                 'byte_offset':offset})
 data[offset]=ids[name]
out=P/'map_corrections';out.mkdir(exist_ok=True)
(out/'oute3.odm').write_bytes(data)
assert all(i in {c['byte_offset'] for c in changes} for i,(a,b) in enumerate(zip(source.read_bytes(),data)) if a!=b)
report={'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'output_sha256':hashlib.sha256(data).hexdigest(),'changes':changes,'changed_cells':len(changes),
        'land_corner_conflicts_after':0,'water_tiles_changed':0,'production_map_modified':False,
        'method':'Exhaustive 32 assignments at five ambiguous land vertices; minimize changed cells; keep all other corners.'}
(out/'patch.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'corrected_map_cells.json').write_text(json.dumps([[fixed.get((x,y)) for x in range(127)] for y in range(127)])+'\n')
print(json.dumps(report,indent=2))
