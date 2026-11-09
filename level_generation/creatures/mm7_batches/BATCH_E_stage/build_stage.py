"""Stage the Batch E models for a later install (not an install): copies the accepted reduced exports into
assets_source/worlds/mm7/models/ and writes assets_dev/worlds/mm7/models/actors.yml, both mirrored under this folder.

Bindings come from each project's README (the `actors.yml` yaml block, tier A); B and C repeat A with their own skin
and, where the README says so, scale_reference to A. Checked against the merged monster table (descriptor names) and
each GLB (material variants, animation clips, bone and socket nodes). Writes manifest.json (sha256 per file).
Args: none. Run from anywhere; install with ./install.sh when the user asks."""
import hashlib, json, re, shutil, struct, sys
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CRE = ROOT / 'level_generation' / 'creatures'
# (project id, tiers B/C take scale_reference to A)
MODELS = [('m162', True), ('m258', False), ('m278', True), ('m402', False), ('m382', False)]
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


def readme_binding(pid):
    text = (CRE / f'mm7_{pid}_claude' / 'README.md').read_text()
    block = re.search(r'```yaml\n(.*?)```', text, re.S).group(1)
    return yaml.safe_load(block)[0]


SRC.mkdir(parents=True, exist_ok=True); DEV.mkdir(parents=True, exist_ok=True)
names = descriptors()
actors, manifest, errors = [], {'files': {}, 'models': {}}, []
for pid, ref in MODELS:
    export = CRE / f'mm7_{pid}_reduce_claude' / 'export' / f'mm7_{pid}.glb'
    target = SRC / export.name
    shutil.copy2(export, target)
    g = glb_json(target)
    variants = {v['name'] for v in g.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])}
    clips = {a['name'] for a in g.get('animations', [])}
    nodes = {n.get('name') for n in g['nodes']}
    a = readme_binding(pid)
    base = a['descriptor'][:-2]
    for tier in 'ABC':
        e = json.loads(json.dumps(a))
        e['descriptor'] = f'{base} {tier}'
        e['skin'] = f'{pid}_{tier.lower()}'
        if tier != 'A' and ref:
            e['scale_reference'] = f'{base} A'
        actors.append(e)
        if e['descriptor'] not in names:
            errors.append(f'{pid}: descriptor not in monster table: {e["descriptor"]}')
        if e['skin'] not in variants:
            errors.append(f'{pid}: skin {e["skin"]} not in GLB variants {sorted(variants)}')
    for role, clip in a['clips'].items():
        if clip not in clips:
            errors.append(f'{pid}: clip {role}={clip} not in GLB {sorted(clips)}')
    anim = a.get('animation', {})
    for key in ('cast', 'run'):
        if key in anim and anim[key] not in clips:
            errors.append(f'{pid}: animation.{key}={anim[key]} not in GLB')
    for node in [anim.get('upper_body_root')] + list(anim.get('look', {}).get('nodes', [])) + list((anim.get('sockets') or {}).values()):
        if node and node not in nodes:
            errors.append(f'{pid}: node {node} not in GLB')
    if a['model'] != f'worlds/mm7/models/{export.name}':
        errors.append(f'{pid}: model path {a["model"]}')
    manifest['models'][pid] = {'export': str(export.relative_to(ROOT)), 'tiers': [f'{base} {t}' for t in 'ABC'],
                               'variants': sorted(variants), 'clips': sorted(clips)}

out = DEV / 'actors.yml'
out.write_text('# MM7 actor model bindings, Batch E (staged; see level_generation/creatures/mm7_batches/BATCH_E_stage/README.md)\n'
               + yaml.safe_dump({'actors': actors}, sort_keys=False, width=120))
for f in sorted(list(SRC.glob('*.glb')) + [out]):
    manifest['files'][str(f.relative_to(HERE))] = hashlib.sha256(f.read_bytes()).hexdigest()
(HERE / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('STAGE', len(actors), 'bindings,', len(list(SRC.glob('*.glb'))), 'models')
for e in errors:
    print('ERROR', e)
sys.exit(1 if errors else 0)
