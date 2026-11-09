"""Spatial calibration from authored encounters, native scenery and actual event faces.

Spawn markers are not actors. Cluster radii are analysis choices, not recovered designer pack IDs.
Do not count Ravenshore's conditional pirate invasion as its baseline wilderness population.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import label
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'level_generation/projects/brackenford_greywatch'
OUT=ROOT/'level_generation/evidence/wilderness_calibration';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file

def xy(p):return [p['x'],p['y']] if isinstance(p,dict) else p[:2]
def quartiles(points):
    if len(points)<2:return None
    return np.percentile(cKDTree(points).query(points,k=2)[0][:,1],[25,50,75]).round(1).tolist()
def clusters(points,radius):
    if not len(points):return []
    points=np.array(points);remaining=set(range(len(points)));out=[]
    while remaining:
        stack=[remaining.pop()];members=[]
        while stack:
            i=stack.pop();members.append(i)
            near={j for j in remaining if np.linalg.norm(points[i]-points[j])<=radius}
            remaining-=near;stack.extend(near)
        out.append(dict(members=sorted(members),count=len(members),center=points[members].mean(0).round(1).tolist()))
    return out

tables={int(r[0]):r for r in csv.reader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt').open(),delimiter='\t') if r and r[0].isdigit()}
stats={r[2]:r for r in csv.reader((ROOT/'assets_dev/engine/data_tables/map_stats.txt').open(),delimiter='\t') if r and r[0].isdigit()}
models={};reports={}
source_paths=[ROOT/'assets_dev/engine/data_tables'/name for name in ['map_stats.txt','terrain_tile_data.txt','monster_data.txt','decoration_data.txt']]
source_paths += [ROOT/'assets_dev/worlds/mm8/events/maps/out02.lua']
for key in ['out02','out08','out06','brackenford_before','brackenford']:
    generated=key.startswith('brackenford');before=key.endswith('_before')
    base=PROJECT/'review/wilderness_revision/before' if before else PROJECT/'source'
    path=base/'lg01.odm' if before else (PROJECT/'runtime/worlds/mm8/maps/lg01.odm' if generated else ROOT/f'assets_dev/worlds/mm8/maps/{key}.odm')
    native=parse_odm_file(path)['payload'];models[key]=native
    if generated:
        semantic=json.loads((base/'lg01.semantic.json').read_text());decor=json.loads((base/'lg01.decorations.json').read_text())['records']
        points=[dict(position=a['position'],family=a['role'],id=a['id']) for a in semantic['fixed_actors'] if a['role'] not in ['guard','villager']]
        source_paths += [base/'lg01.semantic.json',base/'lg01.decorations.json']
        scene={};spawns=[];fixed_count=len(semantic['fixed_actors']);point_kind='fixed hostile actors'
        targets=[dict(name=b['id'],event=b['id'],xy=b['position'][:2]) for b in semantic['content_landmarks'] if b['kind']=='chest_target']
        targets += [dict(name='cave',event=2,xy=[15360,-17154]),dict(name='castle',event=1,xy=[15360,15999])]
    else:
        scene_path=path.with_suffix('.scene.yml');source_paths += [scene_path,ROOT/f'level_generation/evidence/mm8/{key}_decorations.json'];scene=yaml.load(scene_path.read_text(),Loader=yaml.CSafeLoader)
        spawns=[p for p in scene['spawns'] if p['type_id']==3]
        points=[dict(position=xy(p['position']),family=stats[key+'.odm'][16+(p['index']-1)*4+1],id=p['spawn_index']) for p in spawns]
        decor=json.loads((ROOT/f'level_generation/evidence/mm8/{key}_decorations.json').read_text())['records']
        fixed_count=len(scene['initial_state']['actors']);point_kind='encounter spawn markers'
        targets=[]
        for mi,m in enumerate(native['bmodels']):
            events={f['cog_triggered_number'] for f in m['faces'] if f['cog_triggered_number']}
            for event in sorted(events):
                if key!='out02' or not (event in [501,502,507] or 81<=event<=100):continue
                faces=[f for f in m['faces'] if f['cog_triggered_number']==event]
                positions=np.array([[m['vertices'][i][k] for k in 'xy'] for f in faces for i in f['vertex_indices']])
                targets.append(dict(name=m['name'],model=mi,event=event,xy=positions.mean(0).round(1).tolist()))
    positions=np.array([xy(p['position']) for p in points])
    families={}
    for family in sorted({p['family'] for p in points}):
        selected=[p for p in points if p['family']==family];coords=[xy(p['position']) for p in selected]
        grouping=clusters(coords,1600)
        families[family]=dict(count=len(selected),points=selected,nearest_neighbor=quartiles(coords),
            clusters_at_1600=grouping,cluster_center_nearest_neighbor=quartiles([g['center'] for g in grouping]),
            cluster_counts_by_radius={str(r):len(clusters(coords,r)) for r in [1200,1600,2400]})
    for target in targets:
        target['nearest_encounter_anchor']=round(float(np.linalg.norm(positions-target['xy'],axis=1).min()),1)
        target['encounter_anchors_within_2048']=int((np.linalg.norm(positions-target['xy'],axis=1)<=2048).sum())
    visible=[d for d in decor if d['visible']]
    scenery={category:dict(count=sum(d['category']==category for d in visible),
        nearest_neighbor=quartiles([d['position'][:2] for d in visible if d['category']==category])) for category in ['trees','plants','rocks','props','lights']}
    regions={'northwest':[-22528,-4096,8192,22528],'northeast':[2048,20480,8192,22528],
             'southwest':[-22528,-4096,-22528,-8192],'southeast':[2048,20480,-22528,-8192]}
    district={}
    for name,(x0,x1,y0,y1) in regions.items():
        selected=[d for d in visible if x0<=d['position'][0]<x1 and y0<=d['position'][1]<y1]
        point_subset=[p for p in positions if x0<=p[0]<x1 and y0<=p[1]<y1]
        district[name]=dict(bounds=[x0,x1,y0,y1],area=(x1-x0)*(y1-y0),scenery=dict(Counter(d['category'] for d in selected)),
            tree_nearest_neighbor=quartiles([d['position'][:2] for d in selected if d['category']=='trees']),encounter_anchor_count=len(point_subset))
    # Full water cells form lake candidates; shores are excluded from area, by design.
    lookup=scene.get('environment',{}).get('tile_set_lookup_indices',[90,126,162,414])
    def resolved(raw):return raw if raw<90 else lookup[(raw-90)//36]+(raw-90)%36
    water=np.array([bool(int(tables[resolved(raw)][6],16)&2) for raw in native['tile_map']]).reshape(128,128)[:127,:127]
    labels,count=label(water);water_components=[]
    for i in range(1,count+1):
        rr,cc=np.where(labels==i)
        if len(rr)<2:continue
        water_components.append(dict(full_water_cells=len(rr),center=[round(float((cc*512-32512).mean())),round(float((32512-rr*512).mean()))],
            bounds=[int(cc.min()*512-32768),int((cc.max()+1)*512-32768),int(32768-(rr.max()+1)*512),int(32768-rr.min()*512)]))
    reports[key]=dict(source=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        point_kind=point_kind,fixed_actor_records=fixed_count,encounter_anchor_count=len(points),families=families,
        targets=targets,scenery=scenery,regions=district,full_water_components=water_components,
        notes='Standard observation windows are coordinate samples, not inferred city boundaries or walkable-area densities.')
    fig,axes=plt.subplots(1,2,figsize=(14,9))
    heights=np.array(native['height_map']).reshape(128,128)*32
    for ax in axes:
        ax.imshow(heights,extent=[-32768,32768,-32768,32768],origin='upper',cmap='terrain',alpha=.42,vmin=0,vmax=6000)
        ax.imshow(np.ma.masked_where(~water,water),extent=[-32768,32256,-32256,32768],origin='upper',
                  cmap=matplotlib.colors.ListedColormap(['#599fd2']),alpha=.65,interpolation='nearest')
        segments=[]
        for m in native['bmodels']:
            for f in m['faces']:
                vertices=[xy(m['vertices'][i]) for i in f['vertex_indices']];segments.extend(zip(vertices,vertices[1:]+vertices[:1]))
        ax.add_collection(LineCollection(segments,colors='#555555',linewidths=.25,alpha=.5))
        ax.set(xlim=(-24576,24576),ylim=(-24576,24576),aspect='equal',xlabel='native X',ylabel='native Y')
        ax.grid(alpha=.2)
    for family,entry in families.items():
        coords=np.array([xy(p['position']) for p in entry['points']]);axes[0].scatter(coords[:,0],coords[:,1],s=18,label=f'{family}: {len(coords)}')
    for target in targets:
        if target['event'] in [501,502,507,1,2]:
            axes[0].annotate(str(target['name']),target['xy'],fontsize=7);axes[0].plot(*target['xy'],'k*')
    for cat,color in [('trees','#247527'),('plants','#c88a22'),('rocks','#686f7c'),('props','#9b448e')]:
        coords=np.array([d['position'][:2] for d in visible if d['category']==cat])
        if len(coords):axes[1].scatter(coords[:,0],coords[:,1],s=8 if cat=='trees' else 3,c=color,label=f'{cat}: {len(coords)}')
    axes[0].set_title(key+' — '+point_kind);axes[1].set_title(key+' — native decoration positions')
    for ax in axes:ax.legend(fontsize=7,loc='upper center',bbox_to_anchor=(.5,-.08),ncol=3)
    fig.tight_layout();fig.savefig(OUT/(key+'.png'),dpi=140);plt.close(fig)

report=dict(sources=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(set(source_paths))],method=__doc__,cluster_radius=1600,units='native map units; 512 per terrain cell',maps=reports,
    ravenshore_baseline={'spawn_markers':59,'wolves':43,'centaurs':16,'count_per_marker':[1,3],
        'expected_actor_total':118,'range':[59,177],'conditional_hidden_pirates':78,'fixed_town_population':65,
        'event_reference':'assets_dev/worlds/mm8/events/maps/out02.lua: event 4; QBits 6/37/58 and Counter(1)',
        'warning':'Expected total comes from marker count and the current map-stat range; not a sampled save or a fixed native actor count.'})
(OUT/'measurements.json').write_text(json.dumps(report,indent=2)+'\n')
for key,r in reports.items():print(key,r['encounter_anchor_count'],{k:v['count'] for k,v in r['scenery'].items()},'water',r['full_water_components'])
print('Ravenshore entrance relationships',[(t['event'],t['nearest_encounter_anchor'],t['encounter_anchors_within_2048']) for t in reports['out02']['targets'] if t['event']>=500])
