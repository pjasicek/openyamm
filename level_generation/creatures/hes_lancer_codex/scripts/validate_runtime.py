"""Validate exported rigs, bindings, tier materials, reduced skin and complete equipped floor bounds."""
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np
import yaml

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent/'claude_shared/floor'))
from glb_pose import Glb, Model

override=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
def asset_path(name):
    return override if override is not None and name=='hes_lancer' else P/f'export/{name}.glb'

actors = yaml.safe_load((P/'integration/actors.yml').read_text())
source = Glb(P/'source/hes_kreegan.glb')
original_clips = {a['name'] for a in source.json['animations'] if a['name'].startswith(('Carbine_', 'Demon_'))}
variants = {'lancer_a','lancer_b','lancer_c','forgemaster'}
report, problems = {}, []

def require(condition, message):
    if not condition:
        problems.append(message)

ready_models = {Path(a['model']).stem for a in actors}
ready_files = ready_models | {Path(x['model']).stem for a in actors for x in a.get('attachments',[])}
for name in sorted(ready_files):
    path = asset_path(name)
    glb = Glb(path)
    doc = glb.json
    require({v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']} == variants, name+' variants')
    require(not any('emissiveTexture' in m for m in doc['materials']), name+' emissive texture')
    shared_textures = {}
    for material in doc['materials']:
        match = re.match(r'(Lancer_(?:Body|Plate))_(?:A|B|C|FORGEMASTER)(.*)$',material['name'])
        if not match:
            continue
        pbr = material.get('pbrMetallicRoughness',{})
        signature = (pbr.get('baseColorTexture',{}).get('index'),pbr.get('metallicRoughnessTexture',{}).get('index'),
                     material.get('normalTexture',{}).get('index'))
        group = match.group(1)+match.group(2)
        require(signature == shared_textures.setdefault(group,signature), name+'/'+group+' baked tier texture')
    for index, accessor in enumerate(doc['accessors']):
        values = glb.accessor(index)
        require(np.isfinite(values).all(), f'{name} accessor {index}: nonfinite values')
    for animation in doc.get('animations', []):
        for sampler in animation['samplers']:
            times = glb.accessor(sampler['input']).ravel()
            require(np.all(np.diff(times)>0), f'{name}/{animation["name"]}: unordered key times')
    meshes = {}
    for mesh in doc['meshes']:
        meshes[mesh['name']] = sum(doc['accessors'][p['indices']]['count']//3 for p in mesh['primitives'])
        for primitive in mesh['primitives']:
            attrs = primitive['attributes']
            if 'WEIGHTS_0' in attrs:
                weights = glb.accessor(attrs['WEIGHTS_0'])
                require(np.allclose(weights.sum(1), 1, atol=2e-4), name+' skin weights')
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                require(mapping['material'] < len(doc['materials']) and max(mapping['variants'])<4, name+' variant mapping')
    report[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'triangles': meshes,
                    'clips': len(doc.get('animations', []))}

for name in sorted(ready_models):
    glb = Glb(asset_path(name))
    model = Model(glb)
    doc = glb.json
    require(original_clips <= set(model.clips), name+' lost source clips')
    bound = [a for a in actors if Path(a['model']).stem == name]
    clips = set(bound[0]['clips'].values()) | {bound[0]['animation']['run']}
    if 'cast' in bound[0]['animation']:
        clips.add(bound[0]['animation']['cast'])
    require(clips <= set(model.clips), name+' missing bound clips')
    nodes = {n.get('name'): i for i,n in enumerate(doc['nodes'])}
    equipment = {}
    for actor in bound:
        require(actor['skin'] in variants, actor['descriptor']+' skin')
        for node in actor['animation']['sockets'].values():
            require(node in nodes, actor['descriptor']+' missing socket '+node)
        for attachment in actor['attachments']:
            key = Path(attachment['model']).stem
            item = Model(Glb(P/f'export/{key}.glb'))
            points = np.vstack([p for p,_ in item.skinned_positions(item.world({}))])
            equipment[key] = (nodes[attachment['node']], np.column_stack([points, np.ones(len(points))]))
    masks = []
    joint_names = np.array([doc['nodes'][j]['name'] for j in model.joints])
    for primitive in model.primitives:
        mesh = doc['meshes'][doc['nodes'][primitive['node']]['mesh']]
        if not primitive['skinned']:
            masks.append(None)
            continue
        positions, triangles = primitive['positions'], primitive['triangles']
        edges = np.unique(np.sort(np.vstack([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]),axis=1),axis=0)
        lengths = np.linalg.norm(positions[edges[:,0]]-positions[edges[:,1]],axis=1)
        edges, lengths = edges[lengths>1e-6], lengths[lengths>1e-6]
        names = joint_names[primitive['joints']]
        mask = {}
        for side in 'LR':
            hand = np.array([[n.startswith(f'B_{side}_') and any(t in n for t in ('Hand','Finger')) for n in row] for row in names])
            arm = np.array([[n.startswith(f'B_{side}_') and any(t in n for t in ('UpperArm','Forearm')) for n in row] for row in names])
            hand = (primitive['weights']*hand).sum(1)>.25
            arm = ((primitive['weights']*arm).sum(1)>.3) & ~hand
            mask[side] = (arm[edges].all(1),hand[edges].all(1))
        masks.append((edges,lengths,mask))
    measurements = {}
    for clip in sorted(clips):
        keys = model.clip_times(clip)
        times = sorted(set(keys+[(a+b)/2 for a,b in zip(keys,keys[1:])]))
        record = {'body_floor_min_m': float('inf'), 'equipment_floor_min_m': {k:float('inf') for k in equipment},
                  'arm_p99': {'L':0.,'R':0.}, 'hand_max': {'L':0.,'R':0.}}
        for time in times:
            world = model.world(model.sample(clip,time))
            posed = model.skinned_positions(world)
            record['body_floor_min_m'] = min(record['body_floor_min_m'], min(float(p[:,1].min()) for p,_ in posed))
            for key,(node,points) in equipment.items():
                low = float((points@world[node].T)[:,1].min())
                record['equipment_floor_min_m'][key] = min(record['equipment_floor_min_m'][key],low)
            for (points,_), data in zip(posed,masks):
                if data is None:
                    continue
                edges,lengths,mask = data
                stretch = np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)/lengths
                for side,(arm,hand) in mask.items():
                    if arm.any():
                        record['arm_p99'][side] = max(record['arm_p99'][side],float(np.percentile(stretch[arm],99)))
                    if hand.any():
                        record['hand_max'][side] = max(record['hand_max'][side],float(stretch[hand].max()))
        require(record['body_floor_min_m'] >= -.02, name+'/'+clip+' body below floor')
        for item,low in record['equipment_floor_min_m'].items():
            require(low >= -.02, name+'/'+clip+'/'+item+' below floor')
        for side in 'LR':
            require(record['arm_p99'][side] <= 2.05, name+'/'+clip+'/'+side+' reduced arm stretch')
            require(record['hand_max'][side] <= 4.5, name+'/'+clip+'/'+side+' reduced hand stretch')
        measurements[clip] = record
        print('RUNTIME_GATE', name, clip, json.dumps(record), flush=True)
    report[name]['poses'] = measurements

report['problems'] = problems
(P/('review/runtime_preflight.json' if override else 'review/runtime_validation.json')).write_text(json.dumps(report,indent=2)+'\n')
print('RUNTIME_VALIDATION', 'FAIL' if problems else 'PASS', problems)
sys.exit(bool(problems))
