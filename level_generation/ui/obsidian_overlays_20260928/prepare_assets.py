#!/usr/bin/env python3
"""Copy review sources, cut the requested frame slices, and describe UI-only spell clipping."""
from pathlib import Path
import csv
import hashlib
import json
import shutil

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ICONS = REPO / 'assets_dev/engine/icons_x2'
records = []


def receipt(path, source=None, **extra):
    data = {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **extra}
    if source:
        data['source'] = str(source.relative_to(REPO))
    records.append(data)
    return data


def copy(source, target):
    target = ROOT / target
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    receipt(target, source)


for name in ['item138', 'item137', 'item178', 'item177', 'item001', 'item004', 'item199', 'item202',
             'item200', 'item082', 'item256', 'book1', 'book3', 'book4', 'terra0000', 'terra0091', 'hglas060', 'hglas001', 'restmain', 'quikref',
             'fr_stats', 'fr_skill', 'fr_award', 'fr_inven', 'parchment', 'scorebg_food']:
    source = ICONS / (name + '.png')
    if not source.exists():
        raise FileNotFoundError(source)
    copy(source, 'assets/original/' + source.name)
for name in ['arrus', 'create', 'lucida', 'smallnum', 'comic']:
    source = REPO / f'assets_dev/engine/fonts/truetype/openyamm_{name}_faithful.ttf'
    copy(source, 'assets/fonts/' + source.name)
copy(REPO / 'level_generation/creatures/mm6_goblin/direct_complete/trimmed_2x/gobsta0.png',
     'assets/original/goblin.png')

# Actual legacy wording and priority colours, for the reference-preserving revision.
def table(relative):
    path = REPO / relative
    with path.open(encoding='cp1252', newline='') as source:
        rows = list(csv.reader(source, delimiter='\t'))
    return rows

data_root = 'assets_dev/engine/data_tables/'
stats = {row[0]: row[1] for row in table(data_root + 'english/stats.txt')[1:] if len(row) > 1}
skills = {row[0]: {'description': row[1], 'mastery': row[2:6]}
          for row in table(data_root + 'english/skill_des.txt')[1:] if len(row) >= 6}
items = {}
for row in table(data_root + 'items.txt'):
    if len(row) >= 17 and row[1] in ['item138','item137','item178','item177','item001','item004',
                                     'item199','item202','item200','item082','item256','book1','book3','book4']:
        items.setdefault(row[1], {'name': row[2], 'value': row[3], 'type': row[10], 'description': row[16]})
awards = [{'id': int(row[0]), 'text': row[1], 'priority': int(row[2])}
          for row in table(data_root + 'english/awards.txt')[1:9]]
content_path = ROOT / 'content.js'
content_path.write_text('"use strict";\nconst originalContent = ' + json.dumps(
    {'stats': stats, 'skills': skills, 'items': items, 'awards': awards}, ensure_ascii=False) + ';\n')
receipt(content_path, data_sources=[data_root + name for name in
        ['english/stats.txt', 'english/skill_des.txt', 'items.txt', 'english/awards.txt']])

font_sources = {
    'SourceSerif4.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/sourceserif4/SourceSerif4%5Bopsz%2Cwght%5D.ttf',
    'SourceSans3.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/sourcesans3/SourceSans3%5Bwght%5D.ttf',
    'SourceSerif4-OFL.txt': 'https://raw.githubusercontent.com/google/fonts/main/ofl/sourceserif4/OFL.txt',
    'SourceSans3-OFL.txt': 'https://raw.githubusercontent.com/google/fonts/main/ofl/sourcesans3/OFL.txt',
}
for name, url in font_sources.items():
    receipt(ROOT / 'assets/fonts' / name, source_url=url)
for name, prompt in [('frame-v1.png', 'frame'), ('vellum-v1.png', 'paper')]:
    receipt(ROOT / 'assets/generated' / name, tool='built-in imagegen', prompt_key=prompt,
            prompt_file='generated_prompts.json', generated_original_unchanged=True)

# The raw generated RGBA is retained. Export exact rectangular cuts, without painting or recolouring.
master = Image.open(ROOT / 'assets/generated/frame-v1.png').convert('RGBA')
frame_box = (48, 72, 1488, 952)
frame = master.crop(frame_box)
frame.save(ROOT / 'assets/generated/frame-cropped.png')
receipt(ROOT / 'assets/generated/frame-cropped.png', source_crop=list(frame_box))
w, h = frame.size
c = 164
cuts = {
    'tl': (0, 0, c, c), 'tr': (w-c, 0, w, c), 'bl': (0, h-c, c, h), 'br': (w-c, h-c, w, h),
    'top': (w//2-128, 0, w//2+128, c), 'bottom': (w//2-128, h-c, w//2+128, h),
    'left': (0, h//2-128, c, h//2+128), 'right': (w-c, h//2-128, w, h//2+128),
}
for name, box in cuts.items():
    path = ROOT / f'assets/generated/frame-{name}.png'
    frame.crop(box).save(path)
    receipt(path, source_crop=list(box))
frame_info = {'source': 'assets/generated/frame-v1.png', 'crop': list(frame_box), 'corner_source_px': c,
              'display_corner_px': 58, 'edge_display_tile_px': 256 * 58 / c, 'slices': cuts,
              'method': 'Exact RGBA cuts. Four fixed-size corners and four tiled edges; no centre slice.'}
(ROOT / 'frame_slices.json').write_text(json.dumps(frame_info, indent=2) + '\n')

alpha = master.getchannel('A')
histogram = alpha.histogram()
centre = alpha.crop((250, 240, 1250, 780))
alpha_report = {
    'source': 'assets/generated/frame-v1.png', 'size': list(master.size), 'mode': master.mode,
    'alpha_range': list(alpha.getextrema()), 'fully_transparent_pixels': histogram[0],
    'fully_transparent_fraction': histogram[0] / (master.width * master.height),
    'centre_sample_box': [250, 240, 1250, 780], 'centre_alpha_range': list(centre.getextrema()),
    'centre_fraction_alpha_above_1': sum(centre.histogram()[2:]) / (centre.width * centre.height),
    'corners_alpha': [alpha.getpixel(point) for point in [(0,0),(1535,0),(0,1023),(1535,1023)]],
    'processing': 'No alpha repair. Original generated RGBA preserved; slices use exact pixel crops.',
}
(ROOT / 'alpha_verification.json').write_text(json.dumps(alpha_report, indent=2) + '\n')

# Polygon masks are display clips in original image coordinates. Source spell pixels are never modified.
# The bounds exclude both the large green glyph and the smaller rune rows, not just one glyph colour.
polygons = {
 'sbf01a': [(0,0),(100,0),(100,83),(24,83),(24,72),(0,72)],
 'sba01a': [(0,0),(70,0),(70,100),(0,100)],
 'sba02a': [(0,0),(100,0),(100,43),(67,43),(67,64),(50,96),(0,96)],
 'sbs01a': [(0,0),(100,0),(100,76),(65,76),(65,60),(44,60),(44,76),(0,76)],
 'sbw05a': [(26,0),(100,0),(100,74),(22,74),(22,66),(0,66),(0,44),(26,44)],
 'sba10a': [(0,0),(100,0),(100,76),(32,76),(32,60),(0,60)],
 'sba08a': [(0,0),(100,0),(100,100),(55,100),(55,80),(72,80),(72,48),(0,48)],
 'sbe05a': [(24,0),(100,0),(100,89),(42,89),(42,74),(0,74),(0,27),(24,27)],
 'sbl06a': [(0,0),(80,0),(80,32),(66,32),(66,100),(0,100)],
 'sbb09a': [(0,0),(100,0),(100,100),(46,100),(46,68),(0,68)],
 'sbf03a': [(0,0),(100,0),(100,80),(60,80),(45,65),(0,65)],
 'sbw03a': [(0,0),(100,0),(100,66),(72,66),(72,82),(51,82),(51,67),(37,67),(37,75),(0,75)],
 'sba03a': [(0,0),(100,0),(100,80),(35,80),(35,57),(0,57)],
 'sbe03a': [(0,0),(100,0),(100,76),(0,76)],
 'sbm03a': [(0,44),(45,44),(45,35),(100,35),(100,100),(0,100)],
 'sbb03a': [(47,0),(100,0),(100,100),(39,100),(39,30),(47,30)],
 'sba06a': [(0,0),(100,0),(100,53.8),(74,53.8),(72.4,60.2),(67.6,67.4),(60.4,73.5),(50.4,76.5),(0,76.5)],
 'sbs07a': [(0,0),(66,0),(66,57),(100,57),(100,100),(0,100)],
 'sbf05a': [(0,0),(100,0),(100,60),(0,60)],
 'sbf08a': [(0,0),(71,0),(71,100),(0,100)],
 'sbde01a': [(0,26),(100,26),(100,100),(0,100)],
 'sbv02a': [(38,0),(100,0),(100,100),(0,100),(0,72),(39,72),(39,42),(38,42)],
}
catalog = {}
for name, polygon in polygons.items():
    source = ICONS / (name + '.png')  # This installed family has its coloured artwork in A.
    copy(source, 'assets/spells/' + source.name)
    image = Image.open(source).convert('RGBA')
    w, h = image.size
    points = [(round(x*w/100, 2), round(y*h/100, 2)) for x,y in polygon]
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    coverage = ImageChops.multiply(image.getchannel('A'), mask)
    box = coverage.point(lambda a: 255 if a > 28 else 0).getbbox()
    x1,y1,x2,y2 = box
    pad = 4
    catalog[name] = {'file': source.name, 'size': [w,h], 'polygon': points,
                     'viewBox': [x1-pad,y1-pad,x2-x1+2*pad,y2-y1+2*pad]}
(ROOT / 'buff_art.json').write_text(json.dumps(catalog, indent=2) + '\n')
(ROOT / 'buff-art.js').write_text('"use strict";\nconst obsidianBuffSources = ' + json.dumps(catalog) + ';\n' +
    'const obsidianBuffBase = new URL("assets/spells/", document.currentScript.src).href;\n' +
    'let obsidianBuffSerial = 0;\n' +
    '''function glyphFreeBuff(name, className = "", alt = "") {
  const entry = obsidianBuffSources[name];
  if (!entry) return null;
  const id = `buff-clip-${++obsidianBuffSerial}`;
  return `<svg class="buff-art ${className}" viewBox="${entry.viewBox.join(" ")}" role="img"
    aria-label="${alt || name}" preserveAspectRatio="xMidYMid meet">
    <defs><clipPath id="${id}"><polygon points="${entry.polygon.map(p => p.join(",")).join(" ")}"/></clipPath></defs>
    <image href="${obsidianBuffBase + entry.file}" width="${entry.size[0]}" height="${entry.size[1]}"
      clip-path="url(#${id})"/></svg>`;
}
''')
(ROOT / 'asset_sources.json').write_text(json.dumps(records, indent=2) + '\n')
print(f'{len(records)} source/slice receipts; {len(catalog)} glyph-free display clips.')
