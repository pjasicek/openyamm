"""Usage: python3 -I scripts/check_doll_grip.py  (writes review/doll_grip/fist_<family>.png, anchors_new.yml)
Computes paperdoll grip anchors for the NEW x1 icons with the repo's anchor generator, then draws where the doll's
closed fist lands (rows anchorY-9 .. anchorY+8: doll types 0/1 draw the fingers 9 px above the anchor, the
engine negating the table's Y values) on every weapon, beside MM6-MM8 references."""
import csv, json, os, shutil, subprocess, sys, tempfile
import yaml
from PIL import Image, ImageDraw
REPO = '/home/pjasicek/github/OpenYAMM'
HERE = REPO + '/level_generation/ui/mm9_item_icons_20261104'
S = HERE + '/review/doll_grip'
os.makedirs(S, exist_ok=True)
TMP = tempfile.mkdtemp(prefix='mm9_grip_')
mm9, eng = TMP + '/mm9_icons', TMP + '/engine_icons'
for d in (mm9, eng):
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
for f in os.listdir(REPO + '/assets_dev/worlds/mm9/icons'):
    shutil.copy(f'{REPO}/assets_dev/worlds/mm9/icons/{f}', mm9)
designs = json.load(open(HERE + '/designs.json'))
for d in designs:
    src = f"{HERE}/items/{d['design_id']}/icon_a_x1.png"
    if not os.path.exists(src):
        src = f"{HERE}/items/{d['design_id']}/old_grip/icon_a_x1.png"
    for i in d['item_ids']:
        shutil.copy(src, f'{mm9}/mm9_item_{i}.png')
rows = list(csv.reader(open(REPO + '/assets_dev/engine/data_tables/items.txt', encoding='cp1252'), delimiter='\t'))
h = next(i for i, x in enumerate(rows) if x and x[0] == 'Item #')
refrows = [dict(zip(rows[h], x)) for x in rows[h + 1:]]
for r in refrows:
    p = f"{REPO}/assets_dev/engine/icons_x2/{r.get('Pic File', '').lower()}.png"
    if r.get('Pic File') and os.path.exists(p) and not os.path.exists(f"{eng}/{r['Pic File']}.png"):
        im = Image.open(p).convert('RGBA'); im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(f"{eng}/{r['Pic File']}.png")
# The generator's manual override for item 75 (Imperial Star) describes the old diagonal art; the new one has an
# upright handle like every other flail, so the generic flail rule applies.
RUN = ("import sys; sys.path.insert(0, 'tools/mm9_import_discovery'); import generate_mm9_item_equipment_visuals as g; "
       "g.MANUAL_ANCHOR_OVERRIDES.clear(); sys.argv = ['g', '--mm9-icons', sys.argv[1], '--engine-icons', sys.argv[2]]; "
       "raise SystemExit(g.main())")
out = subprocess.run([sys.executable, '-c', RUN, mm9, eng], cwd=REPO, capture_output=True, text=True)
if out.returncode:
    print(out.stderr[-2000:]); sys.exit(1)
anchors = yaml.safe_load(out.stdout)['items']
open(S + '/anchors_new.yml', 'w').write(out.stdout)
mm9rows = list(csv.reader(open(REPO + '/assets_dev/worlds/mm9/data_tables/items.txt', encoding='utf-8'), delimiter='\t'))
h9 = next(i for i, x in enumerate(mm9rows) if x and x[0] == 'Item #')
raw = {int(dict(zip(mm9rows[h9], x))['Item #']): int(dict(zip(mm9rows[h9], x))['x_mm9_raw_item_id'] or 0) for x in mm9rows[h9 + 1:] if x and x[0].isdigit()}
refs = {int(r['Item #']): r for r in refrows if r.get('Item #', '').isdigit()}

def cell(im, ay, ax, label):
    im = im.copy(); dr = ImageDraw.Draw(im, 'RGBA')
    dr.rectangle((ax - 8, ay - 9, ax + 7, ay + 8), fill=(255, 40, 40, 110), outline=(255, 60, 60, 255))
    return im, label

def sheet(name, cells):
    cells = [(c.resize((c.width * 2, c.height * 2), Image.NEAREST), l) for c, l in cells]
    W = sum(c.width + 14 for c, _ in cells) + 10; H = max(c.height for c, _ in cells) + 30
    s = Image.new('RGBA', (W, H), (30, 27, 24, 255)); dr = ImageDraw.Draw(s); x = 8
    for c, l in cells:
        s.alpha_composite(c, (x, H - 4 - c.height)); dr.text((x, 3), l, fill=(200, 190, 170)); x += c.width + 14
    s.convert('RGB').save(f'{S}/{name}.png'); print(name, s.size)

fams = {}
for d in designs:
    fams.setdefault(d['family'], []).append(d)
for fam, lst in fams.items():
    if fam in ('shield', 'bow', 'crossbow', 'firearm') or not any(raw.get(d['design_id']) in anchors for d in lst):
        continue
    cells = []
    for d in lst:
        a = anchors.get(raw.get(d['design_id']))
        if not a: continue
        p = f"{HERE}/items/{d['design_id']}/icon_a_x1.png"
        im = Image.open(p if os.path.exists(p) else f"{HERE}/items/{d['design_id']}/old_grip/icon_a_x1.png").convert('RGBA')
        ax, ay = a['equip_anchor']
        cells.append(cell(im, ay, ax, f"{str(d['design_id'])[-3:]}"))
        r = refs[a['reference_item_id']]
        rim = Image.open(f"{eng}/{r['Pic File']}.png").convert('RGBA')
        cells.append(cell(rim, int(r['Equip Y']), int(r['Equip X']), f"ref{r['Item #']}"))
    sheet('fist_' + fam, cells)
shutil.rmtree(TMP)
