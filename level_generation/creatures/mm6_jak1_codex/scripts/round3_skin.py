"""Round 3: change only skin-ramp metadata; retain every GLB binary byte."""
import copy, hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
sys.dont_write_bytecode = True
P = Path(__file__).resolve().parents[1]
R = P / 'review/round3'
sys.path.insert(0, str(P.parents[2] / 'tools'))
from merge_head_material import read_glb, write_glb
W = np.array([.2126, .7152, .0722])
def lin(c):
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def srgb(c):
    return np.where(c <= .0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - .055)
def stats(c):
    return {'mean_srgb_255': float(np.mean(c)), 'p95_srgb_255': float(np.percentile(c, 95))}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
old, current, samples = [], [], {}
for tag, layer in [('body', 'UVMap'), ('head', 'HeadUV')]:
    core = (np.asarray(Image.open(P / f'textures/jak1_{tag}_material_classes.png')) == 1)
    core &= np.load(P / f'work/uvraster_{layer}.npz')['piece'] >= 0
    values = []
    for root in [P / 'review/round2/before', R / 'before']:
        rgb = np.asarray(Image.open(root / f'textures/jak1_{tag}_basecolor_1k.png').convert('RGB')) / 255
        values.append(srgb(lin(rgb) @ W)[core] * 255)
    old.append(values[0]); current.append(values[1]); samples[tag] = values
old = np.concatenate(old); current = np.concatenate(current)
a = np.array(list(stats(old).values())); b = np.array(list(stats(current).values()))
x, counts = np.unique(lin(current / 255), return_counts=True)
p95 = lin(np.percentile(current, 95) / 255)
knots = np.linspace(0, 1, 16)
def metric(colors):
    return np.array([np.average(srgb(np.interp(x, knots, colors)) * 255, weights=counts),
                     srgb(np.interp(p95, knots, colors)) * 255])
fit = least_squares(lambda z: (metric(z[0] * knots ** z[1]) - (.7 * a + .3 * b)) / (b - a),
                    [.3, .8], bounds=([.01, .1], [1, 3]))
colors = fit.x[0] * knots ** fit.x[1]
assert np.all(np.diff(colors) > 0) and colors.max() <= 1
fraction = (metric(colors) - a) / (b - a)
assert np.all(np.abs(fraction - .3) < 1e-5)
ramp = {'range': [0.0, 1.0], 'colors': [[float(v)] * 3 for v in colors]}
report = {'target_fraction': .30, 'achieved_fraction_mean_p95': fraction.tolist(),
          'method': 'Pooled valid body/head source-UV skin texels; linear Rec.709 luminance encoded to sRGB 0-255. Gold, cloth, eyes and unused UV pixels excluded. Same samples for all three tiers. Monotone power curve sampled into the loader-required 16 linear RGB ramp colours.',
          'power_curve': {'gain': float(fit.x[0]), 'exponent': float(fit.x[1])},
          'skin_ramp': ramp, 'sample_count': len(old), 'tiers': {}}
new = srgb(np.interp(lin(current / 255), knots, colors)) * 255
for tier in ['jak1_a', 'jak1_b', 'jak1_c']:
    report['tiers'][tier] = {'round1': stats(old), 'round2': stats(current), 'round3': stats(new)}
report['regions'] = {tag: {'round1': stats(v[0]), 'round2': stats(v[1]),
    'round3': stats(srgb(np.interp(lin(v[1] / 255), knots, colors)) * 255)} for tag, v in samples.items()}
for name in ['jak1_ramps.json', 'jak1_ramps_runtime.json']:
    path = P / 'textures' / name
    original = json.loads((R / 'before/textures' / name).read_text()); edited = copy.deepcopy(original)
    for mat in edited['materials']:
        for regions in mat['ramps'].values():
            assert len(regions) == 2
            regions[1] = copy.deepcopy(ramp)
    check = copy.deepcopy(edited)
    for i, mat in enumerate(check['materials']):
        for tier, regions in mat['ramps'].items():
            regions[1] = original['materials'][i]['ramps'][tier][1]
    assert check == original
    path.write_text(json.dumps(edited, indent=2))
parity = {}
for name in ['mm6_jak1.glb', 'mm6_jak1_combined.glb', 'mm6_jak1_body_unmerged.glb']:
    path = P / 'export' / name
    original, binary = read_glb(R / 'before/export' / name)
    existing, existing_binary = read_glb(path)
    assert existing_binary == binary, 'This one-time palette repair requires the accepted round-2 binary'
    for i, mat in enumerate(existing['materials']):
        if 'openyamm_region_ramps' in mat.get('extras', {}):
            mat['extras']['openyamm_region_ramps'][1] = original['materials'][i]['extras']['openyamm_region_ramps'][1]
    assert existing == original, 'Unrelated export metadata changed; do not replay this repair'
    edited = copy.deepcopy(original)
    for mat in edited['materials']:
        regions = mat.get('extras', {}).get('openyamm_region_ramps')
        if regions:
            assert len(regions) == 2
            regions[1] = copy.deepcopy(ramp)
    write_glb(path, edited, bytearray(binary))
    checked, checked_binary = read_glb(path)
    assert checked_binary == binary
    for i, mat in enumerate(checked['materials']):
        if 'openyamm_region_ramps' in mat.get('extras', {}):
            mat['extras']['openyamm_region_ramps'][1] = original['materials'][i]['extras']['openyamm_region_ramps'][1]
    assert checked == original, name
    parity[name] = {'before': sha(R / 'before/export' / name), 'after': sha(path),
                    'binary_sha256': hashlib.sha256(binary).hexdigest(),
                    'binary_identical': True, 'all_json_except_skin_ramp_identical': True}
for name in ['export/mm6_jak1_staff.glb', 'integration/actors.yml', 'source/mm6_jak1.blend',
             'export/mm6_jak1_runtime_lod0.glb', 'export/mm6_jak1_lods.glb']:
    assert (P / name).read_bytes() == (R / 'before' / name).read_bytes()
    parity[name] = {'sha256': sha(P / name), 'byte_identical': True}
for path in (R / 'before/textures').rglob('*'):
    if path.is_file() and path.suffix != '.json':
        assert path.read_bytes() == (P / path.relative_to(R / 'before')).read_bytes()
report['parity'] = parity
(R / 'skin_luminance.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'luminance': report['tiers']['jak1_a'], 'fraction': fraction.tolist(), 'parity': parity}, indent=2))
