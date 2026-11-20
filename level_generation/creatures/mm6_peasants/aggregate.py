"""Final eight-family comparison and shared shipping/decoded totals; requires completed packages."""
import hashlib
import json
from PIL import Image, ImageDraw
from prepare_family import HERE, REPO, native
from package_family import animation

inventory = json.loads((HERE / 'inventory.json').read_text())
assert set(inventory) == {'pfem', 'fmp', 'mfp', 'natf', 'pman', 'pmn2', 'mep', 'natm'}
row_height = max(i['logical_canvas'][1] for i in inventory.values()) + 48
contact = Image.new('RGB', (1800, row_height * 8), (43, 45, 43))
draw = ImageDraw.Draw(contact)
families = {}
for row, (family, inv) in enumerate(inventory.items()):
    root = HERE.parent / f'mm6_{family}'
    manifest = json.loads((root / 'manifest.json').read_text())
    validation = json.loads((root / 'validation.json').read_text())
    assert (root / 'README.md').exists() and (root / 'review.html').exists()
    assert set(manifest['frames']) == set(inv['sources']), family
    assert set(manifest['variants']) == set(inv['variants']), family
    for check in ['source_hashes_unchanged', 'raw_cells_unclipped', 'exact_crop_reconstruction',
                  'exact_atlas_extraction', 'variant_alpha_unchanged', 'zero_mask_unchanged', 'base_bypass_exact']:
        assert validation[check] is True, (family, check)
    if family == 'pmn2':
        # The reused package's existing validator records a scalar total.
        assert validation['residual_candidates_above_16'] == 0
    else:
        assert all(n == 0 for n in validation['residual_candidates_above_16'].values()), family
    for palette, variant in inv['variants'].items():
        actual = manifest.get('animations_by_palette', {}).get(palette, manifest['animations'])
        if family == 'pmn2':
            # Its established package stores the shared attack once. The native
            # descriptor's second attack is exactly the same group for all palettes.
            assert variant['actions']['attack2'] == variant['actions']['attack']
            actual = dict(actual, attack2=actual['attack'])
        assert set(actual) == set(variant['actions']), family
        for action, group in variant['actions'].items():
            expected = animation(group, action, manifest['frames'])
            for view, steps in expected['views'].items():
                sequence = actual[action]['views'][view]
                assert len(sequence) == len(steps), (family, palette, action, view)
                for a, e in zip(sequence, steps):
                    assert all(a[k] == e[k] for k in ['frame','duration_ms','mirrored'])
                    assert a.get('native_scale', manifest['native_frame_scale']) == e['native_scale']
    if family == 'pmn2':
        assert (HERE / 'pmn2_reuse_check.json').exists()
    else:
        acceptance = json.loads((root / 'review_acceptance.json').read_text())
        assert acceptance['status'] == 'accepted offline restoration'
        for path, digest in acceptance['reviewed_artifacts'].items():
            assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, (family, path)
    for name, s in inv['sources'].items():
        assert hashlib.sha256((REPO / s['path']).read_bytes()).hexdigest() == s['sha256']
    canvas = manifest['logical_canvas']
    pivot = manifest['logical_pivot']
    baseline = (row + 1) * row_height - 12
    for col, palette in enumerate(inv['variants']):
        anim = manifest.get('animations_by_palette', {}).get(palette, manifest['animations'])
        step = anim['standing']['views']['0'][0]
        name = step['frame']
        original = native(name, int(palette), canvas)
        x = col * 600
        native_x = round(x + 150 - pivot[0])
        bounds = original.getchannel('A').getbbox()
        assert x <= native_x+bounds[0] and native_x+bounds[2] <= x+300
        contact.paste(original, (native_x, baseline - canvas[1]), original)
        f = manifest['frames'][name]
        page = manifest['pages'][f['page']]
        sx, sy, w, h = f['atlas_xywh']
        tile = Image.open(root / page['variant_previews'][palette]).crop((sx, sy, sx + w, sy + h))
        scale = manifest['pixels_per_logical_pixel']
        tile = tile.convert('RGBa').resize((round(w / scale), round(h / scale)), Image.Resampling.LANCZOS).convert('RGBA')
        ox, oy = f['crop_origin_px']
        enhanced_x = round(x + 450 + ox / scale - pivot[0])
        assert x+300 <= enhanced_x and enhanced_x+tile.width <= x+600
        contact.paste(tile, (enhanced_x,
                            round(baseline + oy / scale - pivot[1])), tile)
        draw.text((x + 8, row * row_height + 6), f'{family} / palette {palette}', fill='white')
        draw.text((x + 105, row * row_height + 23), 'Native', fill='#cbd1cb')
        draw.text((x + 400, row * row_height + 23), 'Enhanced', fill='#cbd1cb')
    pixels = sum(p['size'][0] * p['size'][1] for p in manifest['pages'])
    assert all(p['base_format'] == 'RGBA8' and p['mask_format'] in ['R8','RGBA8'] for p in manifest['pages'])
    mask_bytes = sum(p['size'][0]*p['size'][1]*{'R8':1,'RGBA8':4}[p['mask_format']] for p in manifest['pages'])
    shipping = (root / 'manifest.json').stat().st_size + sum(
        (root / p[k]).stat().st_size for p in manifest['pages'] for k in ['base', 'mask'])
    families[family] = dict(native_files=len(inv['sources']), palettes=list(manifest['variants']),
        decoded_base_bytes=pixels * 4, decoded_mask_bytes=mask_bytes,
        mask_formats=sorted({p['mask_format'] for p in manifest['pages']}),
        decoded_shared_bytes=pixels * 4+mask_bytes, shipping_bytes=shipping,
        status='reused; prior separate runtime installation' if family == 'pmn2' else 'staged; not installed',
        page_sha256={p[k]:hashlib.sha256((root/p[k]).read_bytes()).hexdigest()
                     for p in manifest['pages'] for k in ['base','mask']},
        manifest_sha256=hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest())
totals = {k: sum(f[k] for f in families.values()) for k in
          ['native_files', 'decoded_base_bytes', 'decoded_mask_bytes', 'decoded_shared_bytes', 'shipping_bytes']}
report = dict(families=families, totals=totals, palette_appearances=24,
              review_sources_and_baked_previews_excluded=True,
              shared_across_actors=True, contact_logical_scale=1,
              note='R8 for single-region families; MEP uses four RGBA8 data channels with separate recolor vectors. Base alpha is independent.')
contact.save(HERE / 'all_family_variants.png')
(HERE / 'footprint.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(totals))
