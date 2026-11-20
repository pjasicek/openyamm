"""Stage the Batch B models for a later install (not an install): copies the accepted reduced exports (bodies and their
staff/wand attachments) into assets_source/worlds/mm7/models/ and writes assets_dev/worlds/mm7/models/actors.yml,
both mirrored under this folder.

Bindings come from each project's staged `integration/actors.yml` (all three tiers, attachments included). Checked
against the merged monster table (descriptor names) and each GLB (material variants, clips, look nodes, sockets,
attachment nodes in the body and in the attachment GLB). Writes manifest.json (sha256 per file).
Args: none. Run from anywhere; install with ./install.sh when the user asks."""
import hashlib, json, shutil, struct, sys
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CRE = ROOT / 'level_generation' / 'creatures'
MODELS = ['m170', 'm174', 'm274', 'm426', 'm290']
SRC = HERE / 'assets_source' / 'worlds' / 'mm7' / 'models'
DEV = HERE / 'assets_dev' / 'worlds' / 'mm7' / 'models'


def glb_json(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n])


def descriptors():
    names = set()
    for line in (ROOT / 'assets_dev' / 'engine' / 'data_tables' / 'monster_descriptors.txt').read_text(errors='replace').splitlines():
        f = line.split('\t')
        if len(f) > 1 and f[0].isdigit():
            names.add(f[1])
    return names


SRC.mkdir(parents=True, exist_ok=True); DEV.mkdir(parents=True, exist_ok=True)
names = descriptors()
actors, manifest, errors = [], {'files': {}, 'models': {}}, []
for pid in MODELS:
    export_dir = CRE / f'mm7_{pid}_reduce_claude' / 'export'
    files = sorted(export_dir.glob(f'mm7_{pid}*.glb'))
    for f in files:
        shutil.copy2(f, SRC / f.name)
    body = glb_json(SRC / f'mm7_{pid}.glb')
    variants = {v['name'] for v in body.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])}
    clips = {a['name'] for a in body.get('animations', [])}
    nodes = {n.get('name') for n in body['nodes']}
    entries = yaml.safe_load((CRE / f'mm7_{pid}_claude' / 'integration' / 'actors.yml').read_text())
    for e in entries:
        actors.append(e)
        if e['descriptor'] not in names:
            errors.append(f'{pid}: descriptor not in monster table: {e["descriptor"]}')
        if e['skin'] not in variants:
            errors.append(f'{pid}: skin {e["skin"]} not in GLB variants {sorted(variants)}')
        if e['model'] != f'worlds/mm7/models/mm7_{pid}.glb':
            errors.append(f'{pid}: model path {e["model"]}')
        for role, clip in e['clips'].items():
            if clip not in clips:
                errors.append(f'{pid}: clip {role}={clip} not in GLB {sorted(clips)}')
        anim = e.get('animation', {})
        for key in ('cast', 'run'):
            if key in anim and anim[key] not in clips:
                errors.append(f'{pid}: animation.{key}={anim[key]} not in GLB')
        for node in [anim.get('upper_body_root')] + list(anim.get('look', {}).get('nodes', [])) + list((anim.get('sockets') or {}).values()):
            if node and node not in nodes:
                errors.append(f'{pid}: node {node} not in GLB')
        for att in e.get('attachments', []):
            path = SRC / Path(att['model']).name
            if not path.exists() or att['model'] != f'worlds/mm7/models/{path.name}':
                errors.append(f'{pid}: attachment {att["model"]} not staged')
                continue
            if att['node'] not in nodes or att['node'] not in {n.get('name') for n in glb_json(path)['nodes']}:
                errors.append(f'{pid}: attachment node {att["node"]} missing in body or {path.name}')
    manifest['models'][pid] = {'exports': [str(f.relative_to(ROOT)) for f in files],
                               'tiers': [e['descriptor'] for e in entries], 'variants': sorted(variants), 'clips': sorted(clips)}

out = DEV / 'actors.yml'
out.write_text('# MM7 actor model bindings, Batch B (staged; see level_generation/creatures/mm7_batches/BATCH_B_stage/README.md)\n'
               + yaml.safe_dump({'actors': actors}, sort_keys=False, width=120))
for f in sorted(list(SRC.glob('*.glb')) + [out]):
    manifest['files'][str(f.relative_to(HERE))] = hashlib.sha256(f.read_bytes()).hexdigest()
(HERE / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('STAGE', len(actors), 'bindings,', len(list(SRC.glob('*.glb'))), 'GLBs')
for e in errors:
    print('ERROR', e)
sys.exit(1 if errors else 0)
