"""Read native ODM vertices; measure physical assemblies, never raw BModel/header bounds.

Convex projected envelopes include roof overhangs; gaps are conservative envelope separations,
not collision clearances. All district selection and assembly membership is recorded in JSON.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np
from scipy.spatial import ConvexHull
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT/'level_generation/projects/brackenford_greywatch'
OUT = PROJECT/'review/density_revision'
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def envelope(native, ids):
    points=np.array([[v[k] for k in 'xyz'] for i in ids for v in native['bmodels'][i]['vertices']])
    xy=np.unique(points[:,:2],axis=0)
    polygon=xy[ConvexHull(xy).vertices]
    return dict(models=ids, polygon=polygon.tolist(), center=((points.min(0)+points.max(0))/2).tolist(),
                floor_z=int(points[:,2].min()))


def gap(a,b):
    a=np.array(a);b=np.array(b)
    # Convex separating-axis test, including touching/overlapping compound envelopes.
    separated=False
    for p in [a,b]:
        edges=np.roll(p,-1,axis=0)-p
        for x,y in edges:
            n=np.array([-y,x]);pa=a@n;pb=b@n
            if pa.max()<pb.min() or pb.max()<pa.min(): separated=True
    if not separated:return 0.0
    best=float('inf')
    for p,q in [(a,b),(b,a)]:
        for v in p:
            for s,t in zip(q,np.roll(q,-1,axis=0)):
                d=t-s;u=np.clip(np.dot(v-s,d)/np.dot(d,d),0,1)
                best=min(best,float(np.linalg.norm(v-(s+u*d))))
    return best


def measure(records):
    n=len(records);centers=np.array([r['center'][:2] for r in records]);ds=np.full((n,n),np.inf)
    for i in range(n):
        for j in range(i):ds[i,j]=ds[j,i]=gap(records[i]['polygon'],records[j]['polygon'])
    cs=np.linalg.norm(centers[:,None]-centers[None,:],axis=2);np.fill_diagonal(cs,np.inf)
    points=np.concatenate([r['polygon'] for r in records]);hull=ConvexHull(points)
    area=sum(ConvexHull(r['polygon']).volume for r in records)
    return dict(buildings=n,nearest_envelope_gap_p25_median_p75=np.percentile(ds.min(1),[25,50,75]).round(1).tolist(),
                nearest_center_p25_median_p75=np.percentile(cs.min(1),[25,50,75]).round(1).tolist(),
                settlement_envelope_area=round(hull.volume),building_envelope_coverage_percent=round(100*area/hull.volume,1),
                building_base_z_range=[min(r['floor_z'] for r in records),max(r['floor_z'] for r in records)])


def build():
    OUT.mkdir(parents=True,exist_ok=True);sets={};sources=[]
    for world,filename in [('mm8','out02'),('mm8','out05')]:
        p=ROOT/f'assets_dev/worlds/{world}/maps/{filename}.odm';native=parse_odm_file(p)['payload']
        sources.append(dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        if filename=='out02':
            ordinary=[i for i in range(8,63) if not 46<=i<=57]+[89]
            groups=[[i] for i in ordinary]+[[66,67],[107,108,109,110],[71,72],[81,82],[46,47,48,49],[50,51,52,53,54],[78,79,80]]
            allhouses=[envelope(native,ids) for ids in groups]
            sets['Ravenshore all houses']=(native,allhouses)
            sets['Ravenshore market district']=(native,[r for r in allhouses if r['center'][0]>11000 and -17500<r['center'][1]<0])
            sets['Ravenshore northwestern lanes']=(native,[r for r in allhouses if r['center'][0]<12000 and -4000<r['center'][1]<5000])
        else:
            sets['Garrote outer village']=(native,[envelope(native,{35:[35,36],37:[37,38],40:[39,40]}.get(i,[i])) for i in [24,25,27,28,29,31,32,35,37,40,41,42,43,44,45,46,47]])
            sets['Garrote service compound']=(native,[envelope(native,[21,22] if i==22 else [i]) for i in [16,17,18,19,20,22]])
    for label,base in [('Brackenford before',OUT/'before'),('Brackenford after',PROJECT/'runtime/worlds/mm8/maps')]:
        p=base/'lg01.odm'
        if not p.exists():continue
        native=parse_odm_file(p)['payload']
        semantic_path=PROJECT/'source/lg01.semantic.json' if label.endswith('after') else base/'lg01.semantic.json'
        semantic=json.loads(semantic_path.read_text())
        model_indices={m['id']:m['index'] for m in semantic['bmodels']}
        assemblies={}
        for building in semantic['buildings']:
            name=building['id'];group=building.get('shared_block',name)
            assemblies.setdefault(group,[]).extend([model_indices[name],model_indices[name+'_door']])
        groups=list(assemblies.values())
        sets[label]=(native,[envelope(native,ids) for ids in groups])
        sources.append(dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    report=dict(method=__doc__,sources=sources,districts={})
    for name,(native,records) in sets.items():
        report['districts'][name]=dict(metrics=measure(records),buildings=records)
        fig,ax=plt.subplots(figsize=(8,8));h=np.array(native['height_map']).reshape(128,128)*32
        xy=np.concatenate([r['polygon'] for r in records]);lo=xy.min(0)-1100;hi=xy.max(0)+1100
        ax.contour((np.arange(128)-64)*512,(64-np.arange(128))*512,h,levels=np.arange(0,8192,256),colors='#aab995',linewidths=.6,alpha=.8)
        # Both source maps use [90,126,162,414]; raw 198+ is their road bank, not table 198.
        table={int(r[0]):r[1] for r in csv.reader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt').open(),delimiter='\t') if r and r[0].isdigit()}
        tiles=np.array(native['tile_map']).reshape(128,128)
        colors=np.zeros((128,128,4))
        for row in range(128):
            for col in range(128):
                raw=int(tiles[row,col]);key=table.get(raw if raw<198 else raw-198+414,'')
                if key.startswith('drsr'):colors[row,col]=[.69,.48,.28,.40]
                elif key.startswith('dirt'):colors[row,col]=[.82,.73,.58,.25]
                elif key.startswith('wtr'):colors[row,col]=[.3,.6,.85,.3]
        ax.imshow(colors,extent=(-32768,32768,-32768,32768),origin='upper',interpolation='nearest')
        for m in native['bmodels']:
            for face in m['faces']:
                if face['attributes'] & 0x2000:continue
                p=np.array([[m['vertices'][i][k] for k in 'xy'] for i in face['vertex_indices']])
                ax.add_patch(Polygon(p,facecolor='#ddddda',edgecolor='#bbbbbb',lw=.2))
        for r in records:
            ax.add_patch(Polygon(r['polygon'],facecolor='#956842',edgecolor='#3f3022',lw=.7))
            ax.text(*r['center'][:2],'/'.join(map(str,r['models'])),fontsize=6,ha='center',va='center')
        ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),aspect='equal',xlabel='Native X units',ylabel='Native Y units',title=name+' — physical building envelopes')
        ax.grid(alpha=.15);fig.tight_layout();fig.savefig(OUT/(name.lower().replace(' ','_')+'.png'),dpi=140);plt.close(fig)
    # A matched map-unit scale is essential: independently fitted thumbnails hide spacing differences.
    fig,axes=plt.subplots(1,3,figsize=(16,5.4))
    for ax,name in zip(axes,['Brackenford before','Brackenford after','Ravenshore market district']):
        records=sets[name][1];points=np.concatenate([r['polygon'] for r in records]);center=(points.min(0)+points.max(0))/2
        for r in records:ax.add_patch(Polygon(r['polygon'],facecolor='#956842',edgecolor='#302820',lw=.6))
        ax.set(xlim=(center[0]-11000,center[0]+11000),ylim=(center[1]-10000,center[1]+10000),aspect='equal',title=name)
        ax.plot([center[0]-9500,center[0]-5404],[center[1]-8500]*2,color='black',lw=3)
        ax.text(center[0]-9500,center[1]-7800,'4096 units',fontsize=8);ax.grid(alpha=.2)
        ax.tick_params(labelsize=7)
    fig.suptitle('Same spatial scale in every panel — brown = physical building envelopes')
    fig.tight_layout();fig.savefig(OUT/'matched_scale_comparison.png',dpi=140);plt.close(fig)
    (OUT/'measurements.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({n:r['metrics'] for n,r in report['districts'].items()},indent=2))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-directory',default='density_revision')
    args=parser.parse_args()
    OUT=PROJECT/'review'/args.review_directory
    build()
