"""Every MM9 GiveExp award: who gives it, for which quest, where the work is and at what monster level.

Run from the repository root; writes output/mm9_balance/quest_xp_audit.tsv and prints a summary.
Sources: assets_dev/worlds/mm9/events/*.script_ir.yml (original SCR commands), *.raw_objects.yml (NPC names),
data_tables/english/quests_overlay.txt (quest notes, QBit 90000 + key), dialogue/rude/*.rude (keys set by dialogue).
"""
import csv, glob, io, math, os, re, statistics as st, sys
sys.path.insert(0, 'tools/mm9_import_discovery')
import inventory_mm9_rework as inv

W = 'assets_dev/worlds/mm9'
CH = {1: 'isleofashes sturmford sturmfordcity beethoven anskramkeep bootcamp',
      2: 'drangheim drangheimprison drangheimcity guberland guberlandcity thjoradmine tasaracademy',
      3: 'thjorgard thjorgardcity thronheim thronheimcity frosgard frosgardcity mountainpass lindisfarne '
         'lindisfarnemonastery chasmofthedead ruinedtemple inventastorca greatgate thearena dookscastle',
      4: 'yorwick lichlab wizardslab connectingtunnels yanmirsfort darkpassageway bathhouse klusoshouse traininghall '
         'verhoffinruins dungeonofsecrets',
      5: 'templeofhonk 1000terrors arslegardcity dragonstadium hallofthegods afterworld'}
chof = {m: c for c, v in CH.items() for m in v.split()}

# Quest notes.
notes = {}
text = open(f'{W}/data_tables/english/quests_overlay.txt', encoding='utf-8', errors='replace').read()
for row in csv.reader(io.StringIO(text), delimiter='\t'):
    if row and row[0].strip().isdigit() and len(row) > 1:
        notes[int(row[0]) - 90000] = ' '.join(row[1].split())

# Monster levels per map.
mons = inv.load_mm9_monsters()
by_class = {}
for m in mons:
    by_class.setdefault(inv.class_key(m.name), m)
by_name = {m.name: m for m in reversed(mons)}
reports = inv.build_map_reports(by_class)
levels = {}
for mid, rep in reports.items():
    lv = sorted(by_name[n].level for n, k in rep.monsters.items() for _ in range(k))
    if lv:
        levels[mid] = (lv[len(lv) // 2], lv[-1], len(lv))

# NPC names by script, per map.
npc = {}
for raw in glob.glob(f'{W}/maps/*.raw_objects.yml'):
    mid = os.path.basename(raw).split('.')[0]
    for o in inv.load_raw_objects(inv.Path(raw)):
        s = o.properties.get('ScriptName')
        if isinstance(s, str) and s:
            npc.setdefault((mid, s.lower()), str(o.properties.get('Name') or o.object_class))

# Keys set by RUDE rows (columns after the next-node column hold key ids): NPC number -> keys.
rude_keys = {}
for f in glob.glob(f'{W}/dialogue/rude/NPC*.rude'):
    for row in csv.reader(open(f, encoding='latin-1')):
        if len(row) > 8 and row[0].strip().isdigit():
            for x in row[6:]:
                if x.strip().isdigit() and int(x) > 0:
                    rude_keys.setdefault(x.strip(), set()).add('NPC' + row[0].strip())

cmds, gives = {}, {}
for f in glob.glob(f'{W}/events/*.script_ir.yml'):
    mid = os.path.basename(f).split('.')[0]
    body = open(f, encoding='utf-8').read()
    for part in body.split('\n- script_id: ')[1:]:
        sid = part.split('\n', 1)[0].strip()
        src = re.search(r'source_path: (\S+)', part).group(1).lower()
        labels = [(int(a), b) for a, b in re.findall(r'- line: (\d+)\n\s+name: (\S+)', part.split('registered_triggers')[0])]
        cs = [(int(l), c.lower(), a.strip().strip("'").replace(',', ' ').split())
              for l, c, a in re.findall(r'- line: (\d+)\n\s+command: (\S+)\n\s+arguments_raw: (.*)', part)]
        cs.sort()
        cmds[(mid, sid)] = (labels, cs, src)
        for l, c, a in cs:
            if c == 'givekey' and a:
                gives.setdefault(a[0], set()).add(mid)

# Include files (United.inc, BankOrb.inc, SixFires.inc, ...) are not expanded in the script IR: parse them here, on
# every map whose scripts include them.
include_maps = {}
for f in glob.glob(f'{W}/events/*.script_ir.yml'):
    mid = os.path.basename(f).split('.')[0]
    for inc in re.findall(r'- line: \d+\n\s+path: (\S+)', open(f, encoding='utf-8').read()):
        include_maps.setdefault(inc.lower(), set()).add(mid)
SCRIPTS = 'mm9/extracted/SCRIPTS/SCRIPTS'
for f in glob.glob(f'{SCRIPTS}/*.inc') + glob.glob(f'{SCRIPTS}/*.INC'):
    name = os.path.basename(f).lower()
    text = open(f, encoding='latin-1').read()
    if not re.search(r'(?im)^\s*giveexp\b', text) or name not in include_maps:
        continue
    consts = {k.lower(): v for k, v in re.findall(r'(?im)^#number\s+(\w+)\s*=\s*(\d+)', text)}
    labels, cs = [], []
    for number, raw in enumerate(text.splitlines(), 1):
        code = raw.split(';', 1)[0].strip()
        if code.startswith(':'):
            labels.append((number, code[1:].strip()))
            continue
        m = re.match(r'(?i)(haskey|givekey|giveexp|givegold)\b[\s,]*(.*)', code)
        if m:
            args = m.group(2).replace(',', ' ').split()
            args = [consts.get(a.lower(), a) for a in args]
            cs.append((number, m.group(1).lower(), args))
    for mid in sorted(include_maps[name])[:1]:
        cmds[(mid, name)] = (labels, cs, name)

rows, seen = [], {}
for (mid, sid), (labels, cs, src) in sorted(cmds.items()):
    for i, (line, c, a) in enumerate(cs):
        if c != 'giveexp' or not a or not a[0].isdigit():
            continue
        amount = int(a[0])
        label = max([lb for lb in labels if lb[0] <= line], default=(0, ''))[1]
        near = cs[max(0, i - 8):i + 4]
        checked = [x[2][0] for x in cs[max(0, i - 8):i] if x[1] == 'haskey' and x[2]]
        # The key an award sets is the givekey just before it, else the first one after (the quest's "done" key).
        before = [x[2][0] for x in cs[max(0, i - 3):i] if x[1] == 'givekey' and x[2]]
        after = [x[2][0] for x in cs[i + 1:i + 4] if x[1] == 'givekey' and x[2]]
        given = before[-1:] or after[:1]
        gold = sum(int(x[2][0]) for x in near if x[1] == 'givegold' and x[2] and x[2][0].isdigit())
        # One award when either matches: the same amount setting the same quest key (one quest, several turn-in
        # places), or the same amount in the same routine of the same script (an "on the quest" and a "without the
        # quest" branch, or one script used on two maps).
        idents = [(amount, given[-1] if given else (checked[-1] if checked else f'{mid}{sid}{line}')),
                  (src, label, amount)]
        known = next((seen[i] for i in idents if i in seen), None)
        if known is not None:
            known[-1].append(mid)
            known[-2].add(f'{src}:{label}')
            for i in idents:
                seen[i] = known
            continue
        where = sorted({m for k in checked for m in gives.get(k, ())} - {mid})
        lv = [levels[m] for m in [mid] + where if m in levels]
        quest = ' / '.join(f'{k}: {notes.get(int(k), "")[:110]}' for k in dict.fromkeys(checked) if k.isdigit())
        row = [chof.get(mid, 0), mid, npc.get((mid, sid), sid), label, src, amount, gold, ' '.join(dict.fromkeys(checked)),
               ' '.join(given), ' '.join(where), max((x[0] for x in lv), default=''), max((x[1] for x in lv), default=''),
               quest, {f'{src}:{label}'}, []]
        for i in idents:
            seen[i] = row
        rows.append(row)
        # Variable amounts (object parameters, g_nPad2) are listed in QUEST_XP_AUDIT.md, not here.

os.makedirs('output/mm9_balance', exist_ok=True)
with open('output/mm9_balance/quest_xp_audit.tsv', 'w', newline='') as out:
    w = csv.writer(out, delimiter='\t')
    w.writerow(['chapter', 'map', 'npc', 'routine', 'script', 'xp', 'gold', 'keys checked', 'keys given', 'key maps',
                'median level', 'max level', 'quest notes', 'occurrences', 'also turned in at'])
    for r in sorted(rows, key=lambda r: (r[0], r[1], -r[5])):
        w.writerow(r[:-2] + [' '.join(sorted(r[-2])), ' '.join(r[-1])])
print(len(rows), 'awards,', sum(r[5] for r in rows), 'XP')
