"""Review proposals for occluded heads using the native gold talon pigment."""
import importlib.util
from pathlib import Path

p = Path(__file__).with_name('session_pipeline.py')
s = importlib.util.spec_from_file_location('session', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
root = m.STAGE / 'mm7_m390'
out = root / 'redo_2x'
sources = m.read(root / 'sources.json')
registration = m.read(out / 'registration.json')
skipped = m.read(out / 'review/beak_translation_proposals.json')['skipped']


def talons(image):
    a = m.np.array(image).astype(float)
    select = ((a[:, :, 3] > 128) & (a[:, :, 0] > 135) &
              (a[:, :, 1] > 75) & (a[:, :, 2] < a[:, :, 0] * 0.12) &
              (a[:, :, 0] > a[:, :, 1] * 1.3) &
              (a[:, :, 0] < a[:, :, 1] * 2.5))
    yy, xx = m.np.nonzero(select)
    return None if len(xx) < 4 else m.np.array([xx.mean(), yy.mean()])


proposals, tiles, missing = {}, [], []
for name in skipped:
    r = registration[name]
    native = m.native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
    clean = m.Image.open(m.REPO / r['clean_path']).convert('RGBA')
    n, c = talons(native), talons(clean)
    if n is None or c is None:
        missing.append(name)
        continue
    n /= 2
    scaled_size = m.np.array([max(1, round(x * r['scale'])) for x in clean.size])
    factor = scaled_size / clean.size
    proposals[name] = dict(native=n.tolist(), clean=c.tolist(), axes=[0, 1],
        raw_sha256=r['raw_sha256'], clean_sha256=m.sha(m.REPO / r['clean_path']),
        landmark='visually_confirmed_gold_talon_pigment_centroid',
        method='Whole-pose translation using visible gold talons when the beak is occluded. Head, wing roots, joints and tail independently reviewed; no resizing or limb warp.')
    restored = m.Image.new('RGBA', native.size)
    scaled = clean.convert('RGBa').resize(tuple(scaled_size), m.Image.Resampling.LANCZOS).convert('RGBA')
    restored.paste(scaled, tuple(m.np.round(n * 2 - c * factor).astype(int)))
    tile = m.Image.new('RGB', (512, 286), (36, 40, 40))
    d = m.ImageDraw.Draw(tile)
    d.text((3, 3), name + ' | native / proposed | gold talon cross', fill='white')
    for i, im in enumerate([native, restored]):
        im = im.resize((256, 256), m.Image.Resampling.LANCZOS)
        tile.paste(im, (i * 256, 22), im.getchannel('A'))
        x, y = n + [i * 256, 22]
        d.line((x - 4, y, x + 4, y), fill=(0, 255, 255))
        d.line((x, y - 4, x, y + 4), fill=(0, 255, 255))
    tiles.append(tile)

for start in range(0, len(tiles), 9):
    page = m.Image.new('RGB', (1536, 858), (36, 40, 40))
    for i, tile in enumerate(tiles[start:start + 9]):
        page.paste(tile, (i % 3 * 512, i // 3 * 286))
    page.save(out / 'review' / f'talon_translation_proposals_{start // 9:02}.png')
m.save(out / 'review/talon_translation_proposals.json', dict(proposals=proposals, missing=missing))
print(len(proposals), 'talon proposals; missing:', missing)
