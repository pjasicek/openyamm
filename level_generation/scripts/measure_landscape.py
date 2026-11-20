"""Compare local scenery density and ground variants on usable land, with explicit settlement masks."""
from pathlib import Path
from collections import Counter
import csv,json,sys,hashlib
import numpy as np
from scipy.spatial import cKDTree,ConvexHull
from scipy.ndimage import gaussian_filter
from matplotlib.path import Path as PlotPath
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'level_generation/projects/brackenford_greywatch'
OUT=ROOT/'level_generation/evidence/landscape_calibration';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'util'));from map_export import parse_odm_file
import yaml
rows={int(r[0]):r for r in csv.reader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt').open(),delimiter='\t') if r and r[0].isdigit()}
report={};fig,axes=plt.subplots(4,3,figsize=(15,19))
for row,key in enumerate(['ravenshore','alvar','brackenford_before','brackenford']):
    generated=key.startswith('brackenford');before=key.endswith('before')
    base=P/'review/landscape_revision/before' if before else P/'source'
    stem='out02' if key=='ravenshore' else 'out03'
    nativepath=(base/'lg01.odm' if before else P/'runtime/worlds/mm8/maps/lg01.odm') if generated else ROOT/f'assets_dev/worlds/mm8/maps/{stem}.odm'
    native=parse_odm_file(nativepath)['payload']
    if generated:
        data=json.loads((base/'lg01.semantic.json').read_text());decorpath=base/'lg01.decorations.json'
        houses=[(b['xy'],b['target_footprint']) for b in data['buildings']];lookup=[90,126,162,414]
    else:
        decorpath=ROOT/f'level_generation/evidence/mm8/{stem}_decorations.json'
        scene=yaml.load(nativepath.with_suffix('.scene.yml').read_text(),Loader=yaml.CSafeLoader);lookup=scene['environment']['tile_set_lookup_indices']
        # Explicit service/residence event faces define settlement reference buildings.
        events=(ROOT/f'assets_dev/worlds/mm8/events/maps/{stem}.lua').read_text(encoding='cp1252')
        import re
        house_events=[]
        for m in re.finditer(r'RegisterEvent\((\d+),.*?(?=RegisterEvent\(|\Z)',events,re.S):
            if 'evt.EnterHouse(' in m.group(0):house_events.append(int(m.group(1)))
        houses=[]
        for b in native['bmodels']:
            if not any(f['cog_triggered_number'] in house_events for f in b['faces']):continue
            v=np.array([[p[k] for k in 'xy'] for p in b['vertices']]);lo=v.min(0);hi=v.max(0)
            houses.append(((lo+hi)/2,hi-lo))
    all_houses=houses
    if not generated:
        # Explicit main-town membership from the native plan: exclude Ravenshore's remote northern
        # windmill and Alvar's far southwestern rural homes, while keeping both sides of town rivers.
        houses=[h for h in houses if (h[0][1]<8192 if key=='ravenshore' else h[0][1]>8192)]
    decor=json.loads(decorpath.read_text())['records'];decor=[d for d in decor if d['visible']]
    if generated:
        assert len(native['entities'])==len(decor)+1, 'Build native geometry before measuring source decoration changes'
        for d in decor:
            entity=native['entities'][d['index']]
            assert entity['name']==d['name'] and [entity['position'][k] for k in 'xyz']==d['position']
    vertices=np.array([[x+sx*w/2,y+sy*h/2] for (x,y),(w,h) in houses for sx,sy in [(-1,-1),(-1,1),(1,1),(1,-1)]])
    hull=vertices[ConvexHull(vertices).vertices];town=PlotPath(hull)
    rr,cc=np.mgrid[:127,:127];xy=np.stack([cc*512-32512,32512-rr*512],axis=-1)
    raw=np.array(native['tile_map']).reshape(128,128)[:127,:127]
    ids=np.vectorize(lambda i:i if i<90 else lookup[(i-90)//36]+(i-90)%36)(raw)
    water=np.vectorize(lambda i:bool(int(rows[i][6],16)&2))(ids)
    land=(~water)&(np.abs(xy[:,:,0])<24576)&(np.abs(xy[:,:,1])<24576)
    inside=town.contains_points(xy.reshape(-1,2)).reshape(raw.shape)
    # Signed hull membership plus distance to authored building envelopes distinguishes core/edge/country.
    distance=np.full(raw.shape,np.inf)
    for (x,y),(w,h) in houses:
        distance=np.minimum(distance,np.hypot(np.maximum(abs(xy[:,:,0]-x)-w/2,0),np.maximum(abs(xy[:,:,1]-y)-h/2,0)))
    masks={'town':land&inside,'town_edge':land&~inside&(distance<=4096),'wilderness':land&~inside&(distance>4096)}
    categories=['trees','rocks','plants'];counts={};fields=[]
    for cat in categories:
        pts=np.array([d['position'][:2] for d in decor if d['category']==cat])
        hist=np.zeros(raw.shape)
        for x,y in pts:
            c=int(np.floor(x/512+64));r=int(np.floor(64-y/512))
            if 0<=r<127 and 0<=c<127:hist[r,c]+=1
        # Same 1536-unit Gaussian for every map. Divide by available-land support near coasts.
        density=gaussian_filter(hist,3)/np.maximum(gaussian_filter(land.astype(float),3),.05)*16
        fields.append(density)
        counts[cat]={name:dict(count=int(hist[mask].sum()),land_cells=int(mask.sum()),
            per_4096_square=round(float(hist[mask].sum()/mask.sum()*64),2)) for name,mask in masks.items()}
    variants={name:dict(Counter(rows[int(i)][1].lower() for i in ids[mask])) for name,mask in masks.items()}
    report[key]=dict(native=str(nativepath.relative_to(ROOT)),sha256=hashlib.sha256(nativepath.read_bytes()).hexdigest(),
        decoration_source=str(decorpath.relative_to(ROOT)),decoration_sha256=hashlib.sha256(decorpath.read_bytes()).hexdigest(),
        town_hull=hull.tolist(),building_count=len(houses),all_house_count=len(all_houses),town_house_centers=[list(map(float,h[0])) for h in houses],scenery=counts,terrain_textures_by_region=variants,
        whole_grid_interior_raw_counts={str(i):native['tile_map'].count(i) for i in list(range(1,13))+list(range(90,102))})
    for j,(cat,field) in enumerate(zip(categories,fields)):
        ax=axes[row,j];im=ax.imshow(np.ma.masked_where(~land,field),origin='upper',extent=[-32768,32256,-32256,32768],vmin=0,vmax={'trees':4,'rocks':3,'plants':8}[cat],cmap='YlGnBu')
        ax.plot(*np.vstack([hull,hull[0]]).T,color='#ef3030',lw=1)
        ax.set(xlim=(-24576,24576),ylim=(-24576,24576),title=key+' — '+cat,aspect='equal')
        fig.colorbar(im,ax=ax,shrink=.8,label='local count per 2048 × 2048 area')
fig.tight_layout();fig.savefig(OUT/'heatmaps.png',dpi=130);plt.close(fig)
(OUT/'measurements.json').write_text(json.dumps(dict(method=__doc__,units='512-unit terrain cells',
    region_method='Convex hull of main-town service/resident envelopes: Ravenshore centers Y<8192, Alvar Y>8192, generated authored town; exterior edge within 4096 of envelopes; full-water cells excluded. Hulls are analytical masks, not official town boundaries.',
    heatmap_method='1536-unit Gaussian; available-land normalization; common color range per category. Sparse source count, not sprite canopy area. Shore cells count as land.',maps=report),indent=2)+'\n')
for k,r in report.items():print(k,r['scenery'])
