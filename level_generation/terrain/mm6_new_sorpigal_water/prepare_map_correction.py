"""Find a small explicit tile-selection correction across land and shore; never edit the source ODM."""
import collections,csv,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import lil_matrix
P=Path(__file__).resolve().parent;C=P.parent/'mm6_new_sorpigal';L=P.parent/'mm6_new_sorpigal_transitions';ROOT=P.parents[2]
sig={r['tile']:tuple(r['corners_NW_NE_SE_SW']) for r in json.loads((L/'mask_inventory.json').read_text())['masks']}
sig.update({n:('dirt',)*4 for n in sig if n.startswith('6drsr')})
sig.update({'6dirttyl':('dirt',)*4,'6grastyl':('grass',)*4,'6voltyl':('volcano',)*4,'6wtrtyl':('water',)*4})
for f in (C/'alpha/shore_visible').glob('*.png'):
 a=np.array(Image.open(f));sig[f.stem]=tuple('dirt' if v else 'water' for v in [a[0,0],a[0,-1],a[-1,-1],a[-1,0]])
grid={(int(r['column']),int(r['row'])):r['texture'] for r in csv.DictReader((C/'map_cells.csv').open())}
ofs=[(0,0),(1,0),(1,1),(0,1)];verts=collections.defaultdict(list)
for (x,y),n in grid.items():
 for i,(dx,dy) in enumerate(ofs):verts[x+dx,y+dy].append((sig[n][i],x,y,n))
bad={k:v for k,v in verts.items() if len({t[0] for t in v})>1}
cells=sorted({(x,y) for vx,vy in bad for y in range(vy-2,vy+2) for x in range(vx-2,vx+2) if (x,y) in grid})
materials=['dirt','grass','volcano','water'];names=sorted(n for n in sig if not n.startswith('6drsr'))
variables=[];cost=[];tilevars={}
for cell in cells:
 original=grid[cell];domain=[original] if original.startswith('6drsr') else names
 tilevars[cell]=[]
 for n in domain:
  tilevars[cell].append((n,len(variables)));variables.append(('tile',cell,n))
  cost.append((n!=original)+.001*sum(a!=b for a,b in zip(sig[n],sig[original])))
vvars={}
for x,y in cells:
 for dx,dy in ofs:
  v=(x+dx,y+dy)
  if v not in vvars:
   vvars[v]={}
   for m in materials:vvars[v][m]=len(variables);variables.append(('vertex',v,m));cost.append(0)
rows=[];rhs=[]
def equation(terms,value):rows.append(terms);rhs.append(value)
for cell,choices in tilevars.items():
 equation({i:1 for n,i in choices},1)
 x,y=cell
 for corner,(dx,dy) in enumerate(ofs):
  for m in materials:
   terms={i:1 for n,i in choices if sig[n][corner]==m};terms[vvars[x+dx,y+dy][m]]=-1;equation(terms,0)
for v,ids in vvars.items():
 equation({i:1 for i in ids.values()},1)
 external={m for m,x,y,n in verts[v] if (x,y) not in tilevars}
 assert len(external)<=1
 if external:equation({ids[next(iter(external))]:1},1)
a=lil_matrix((len(rows),len(variables)))
for r,terms in enumerate(rows):
 for i,value in terms.items():a[r,i]=value
result=milp(np.array(cost),integrality=np.ones(len(variables)),bounds=Bounds(0,1),constraints=LinearConstraint(a.tocsr(),rhs,rhs),options={'time_limit':60})
assert result.success,result.message
fixed=dict(grid);changes=[]
for cell,choices in tilevars.items():
 selected=[n for n,i in choices if result.x[i]>.5];assert len(selected)==1
 if selected[0]!=grid[cell]:fixed[cell]=selected[0];changes.append({'column':cell[0],'row':cell[1],'before':grid[cell],'after':selected[0]})
for (x,y),n in fixed.items():
 for dx,dy,ai,bi in [(1,0,(1,2),(0,3)),(0,1,(3,2),(0,1))]:
  b=fixed.get((x+dx,y+dy))
  if b:assert tuple(sig[n][i] for i in ai)==tuple(sig[b][i] for i in bi),(x,y,n,b)
cat=json.loads((C/'catalogue.json').read_text());ids={t['name']:t['raw_tile_ids'][0] for t in cat['tiles']}
sys.path.insert(0,str(ROOT/'util'));import map_export
source=ROOT/cat['source_map'];data=bytearray(source.read_bytes());native=map_export.parse_odm_file(source)['payload']
offset=(map_export.TERRAIN_SECTION_OFFSET_V8 if native['version']==8 else map_export.TERRAIN_SECTION_OFFSET)+map_export.TERRAIN_MAP_SIZE
for c in changes:
 k=offset+c['row']*128+c['column'];c.update(byte_offset=k,before_raw_id=data[k],after_raw_id=ids[c['after']]);data[k]=ids[c['after']]
assert {i for i,(a,b) in enumerate(zip(source.read_bytes(),data)) if a!=b}=={c['byte_offset'] for c in changes}
out=P/'map_correction';out.mkdir(exist_ok=True);(out/'oute3.odm').write_bytes(data)
(out/'patch.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(data).hexdigest(),'changes':changes,'changed_cells':len(changes),'production_modified':False,'method':'Minimum changed tiles within 4x4 neighbourhoods of six conflicting vertices, with a secondary corner-change cost; all land/water corners constrained'},indent=2)+'\n')
(P/'corrected_map_cells.json').write_text(json.dumps([[fixed[x,y] for x in range(127)] for y in range(127)])+'\n')
print('Prepared optional corrected map:',len(changes),'tile bytes changed; all material corners agree.')
