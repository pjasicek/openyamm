"""Native road/heightfield continuation beyond travel bounds, measured on rendered 127x127 cells."""
from pathlib import Path
import csv,hashlib,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'level_generation/projects/brackenford_greywatch'
OUT=ROOT/'level_generation/evidence/transition_calibration';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'util'));from map_export import parse_odm_file
nav={r[0].lower():r for r in csv.reader((ROOT/'assets_dev/engine/data_tables/map_navigation.txt').open(),delimiter='\t') if r and not r[0].startswith('/')}
fig,axes=plt.subplots(5,2,figsize=(15,24));reports=[]
sets=[('ravenshore','out02',['east','north','west']),('alvar','out03',['west','east','south']),('brackenford_before','lg01',['west','north']),('brackenford','lg01',['west','north'])]
for name,stem,sides in sets:
    if stem=='lg01':
        path=P/('review/transition_revision/before/lg01.odm' if name.endswith('before') else 'runtime/worlds/mm8/maps/lg01.odm');bounds=[-24576,24576,-24576,24576]
    else:path=ROOT/f'assets_dev/worlds/mm8/maps/{stem}.odm';bounds=list(map(int,nav[stem+'.odm'][1:5]))
    native=parse_odm_file(path)['payload'];raw=np.array(native['tile_map']).reshape(128,128)[:127,:127];height=np.array(native['height_map']).reshape(128,128)*32
    rr,cc=np.indices(raw.shape);xx=cc*512-32512;yy=32512-rr*512;roads=(raw>=198)&(raw<234)
    for side in sides:
        direction={'east':xx,'west':-xx,'north':yy,'south':-yy}[side];threshold=abs(bounds[{'west':0,'east':1,'south':2,'north':3}[side]])
        outside=roads&(direction>threshold)
        transverse=xx if side in ('north','south') else yy
        mask=roads&(direction>threshold-4096)&(transverse>=transverse[outside].min()-2048)&(transverse<=transverse[outside].max()+2048)
        r,c=np.where(mask);assert len(r)
        x=xx[r,c];y=yy[r,c]
        extent=float(direction[outside].max()+256)
        record=dict(map=name,side=side,source=str(path.relative_to(ROOT)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            travel_boundary=threshold,last_road_outer_coordinate=extent,scenery_extension=extent-threshold,
            road_cells_beyond_trigger=int(outside.sum()),road_xy_extent=[int(x.min()-256),int(x.max()+256),int(y.min()-256),int(y.max()+256)],
            rendered_terrain_bounds=[-32768,32256,-32256,32768])
        ax=axes.flat[len(reports)];reports.append(record)
        ax.imshow(height,origin='upper',extent=[-33024,32512,-32512,33024],cmap='terrain',vmin=0,vmax=8160)
        for row,col in zip(r,c):ax.add_patch(Rectangle((xx[row,col]-256,yy[row,col]-256),512,512,facecolor='#fa4444',edgecolor='none'))
        horizontal=side in ('north','south');value=bounds[{'west':0,'east':1,'south':2,'north':3}[side]]
        (ax.axhline if horizontal else ax.axvline)(value,color='#00efff',lw=2,ls='--',label='travel trigger')
        if horizontal:ax.set_xlim(x.min()-4096,x.max()+4096);ax.set_ylim((-32768,-18000) if side=='south' else (18000,33280))
        else:ax.set_ylim(y.min()-4096,y.max()+4096);ax.set_xlim((-33280,-18000) if side=='west' else (18000,32768))
        ax.set_aspect('equal');ax.set_title(f'{name}: {side}\nroad continues {extent-threshold:,.0f} units beyond trigger');ax.legend(loc='upper right',fontsize=8)
fig.suptitle('Red: native road cells • Cyan: travel boundary • Relief: native elevation\nRendered cells only; final stored row/column have no terrain quad',fontsize=14)
fig.tight_layout(rect=(0,0,1,.94));fig.savefig(OUT/'exit_plans.png',dpi=120);plt.close(fig)
report=dict(method=__doc__,terrain_mesh_bounds=[-32768,32256,-32256,32768],cell_size=512,height_quantum=32,
    navigation_sha256=hashlib.sha256((ROOT/'assets_dev/engine/data_tables/map_navigation.txt').read_bytes()).hexdigest(),
    limitations='Road-family cells in edge strips, not a claim of painted-edge connectivity or complete traversal. Existing native MM8 road bank is raw198-233. Flying can reveal the finite mesh.',exits=reports)
(OUT/'measurements.json').write_text(json.dumps(report,indent=2)+'\n')
for r in reports:print(r['map'],r['side'],r['scenery_extension'],r['road_cells_beyond_trigger'])
