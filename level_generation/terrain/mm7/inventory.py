"""Inventory MM7 rendered terrain using the runtime descriptor lookup, with source hashes."""
import collections, csv, hashlib, json, sys
from pathlib import Path
from PIL import Image, ImageDraw
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
GROUPS={'dirt':('7dirttyl',None),'grass':('7grastyl','7grdrt'),'sand':('7sand','7sddrt'),
        'snow':('7snow','7sndrt'),'swamp':('7swtyl','7swdrt'),'waste':('7wastetile','7wstdrt'),
        'roads':(None,'7drsr'),'shore':(None,'7hwtrdr'),'water':('7wtrtyl','7hdwtr')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def family(n):
 for g,(base,prefix) in GROUPS.items():
  if n==base or prefix and n.startswith(prefix):return g
 if n.startswith('7dirt'):return 'dirt'
 if n.startswith('7swtyl'):return 'swamp'
 raise ValueError(n)
def main():
 tablepath=ROOT/'assets_dev/engine/data_tables/terrain_tile_data_2.txt'
 table=list(csv.DictReader(tablepath.open(),delimiter='\t'))
 titles={r[2].lower():r[1] for r in csv.reader((ROOT/'assets_dev/engine/data_tables/map_stats.txt').open(),delimiter='\t') if len(r)>2}
 maps=[];used=collections.defaultdict(dict);descriptors=collections.defaultdict(dict);grids={}
 for p in sorted((ROOT/'assets_dev/worlds/mm7/maps').glob('*.odm')):
  d=parse_odm_file(p)['payload'];names=[]
  assert len(d['tile_map'])==16384
  for raw in d['tile_map']:
   assert raw<234
   i=raw if raw<90 or d['master_tile']>=3 else d['tile_set_lookup_indices'][(raw-90)//36]+(raw-90)%36
   n=table[i]['texture_name'].lower();assert n!='pending'
   names.append(n);descriptors[n][i]=table[i]
  grid=[names[y*128:y*128+127] for y in range(127)];grids[p.stem]=grid
  counts=collections.Counter(n for row in grid for n in row)
  for n,count in counts.items():used[n][p.stem]=count
  maps.append(dict(id=p.stem,title=titles.get(p.name,p.stem),source=str(p.relative_to(ROOT)),sha256=sha(p),master_tile=d['master_tile'],lookup=d['tile_set_lookup_indices'],tiles=dict(sorted(counts.items()))))
 src={p.stem.lower():p for p in (ROOT/'assets_dev/worlds/mm7/textures').glob('*.bmp')}
 src.update({p.stem.lower():p for p in (ROOT/'assets_dev/engine/terrain').glob('*.bmp')})
 mm6={}
 for p in (ROOT/'assets_dev/worlds/mm6/textures').glob('*.bmp'):
  im=Image.open(p).convert('RGB');mm6.setdefault(hashlib.sha256(im.tobytes()).hexdigest(),[]).append(p.stem)
 records=[]
 for n in sorted(set(used)|{f'7hdwtr{i:03}' for i in range(14)}):
  p=src[n];im=Image.open(p);g=family(n);base,prefix=GROUPS[g]
  (P/'references').mkdir(exist_ok=True);im.convert('RGB').save(P/'references'/f'{n}.png')
  records.append(dict(name=n,family=g,kind='animation' if n.startswith('7hdwtr') else 'base' if n==base else 'variant' if n in ['7dirt1','7dirt2','7swtylv1','7swtylv2'] else 'shore' if g=='shore' else 'transition',source=str(p.relative_to(ROOT)),sha256=sha(p),size=list(im.size),maps=used.get(n,{}),descriptors=list(descriptors[n].values()),identical_mm6=mm6.get(hashlib.sha256(im.convert('RGB').tobytes()).hexdigest(),[])))
 (P/'inventory.json').write_text(json.dumps(dict(table=str(tablepath.relative_to(ROOT)),table_sha256=sha(tablepath),rendered_size=[127,127],groups=GROUPS,maps=maps,tiles=records),indent=2)+'\n')
 (P/'grids.json').write_text(json.dumps(grids)+'\n')
 (P/'sheets').mkdir(exist_ok=True)
 for g in GROUPS:
  rows=[r for r in records if r['family']==g];sheet=Image.new('RGB',(4*192,((len(rows)+3)//4)*216),'#202933');draw=ImageDraw.Draw(sheet)
  for i,r in enumerate(rows):
   x,y=i%4*192,i//4*216;sheet.paste(Image.open(P/'references'/f"{r['name']}.png").resize((192,192)),(x,y+24));draw.text((x+4,y+6),r['name'],fill='white')
  sheet.save(P/'sheets'/f'{g}.png')
 print(json.dumps(dict(maps=len(maps),static=len(used),total=len(records),groups=dict(collections.Counter(r['family'] for r in records)),identical_mm6={r['name']:r['identical_mm6'] for r in records if r['identical_mm6']}),indent=2))
if __name__=='__main__':main()
